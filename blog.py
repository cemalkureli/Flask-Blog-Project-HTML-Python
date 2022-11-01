from ast import keyword
import email
import imp
from operator import imod
import re
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt 
from functools import wraps


# Kullanıcı Giriş Decorator'ı 

def login_required(f): 
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs) # Kontrolden sonra herhangi bir fonksiyonu (hangi fonksiyon çağırılıyorsa) aynı şekilde çağırmasını sağlar. 
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız.","danger")
            return redirect(url_for("login"))

    return decorated_function

# Kullanıcı Kayıt Formu

class RegisterForm(Form):
    name = StringField("İsim/Soyisim",validators=[validators.Length(max=25,min=4,message="Min = 4 / Max = 25 uzunluğunda olmalıdır."),validators.DataRequired(message = "Boş Bırakılamaz.")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(max=35,min=5,message="Min = 5 / Max = 35 uzunluğunda olmalıdır."),validators.DataRequired(message = "Boş Bırakılamaz.")])
    email = StringField("E-Mail",validators=[validators.Email(message = "Lütfen Geçerli Bir E-mail Adresi Giriniz."),validators.DataRequired(message = "Boş Bırakılamaz.")])
    password = PasswordField("Parola:",validators = [validators.DataRequired(message="Boş Bırakılamaz.")])
    confirm_password = PasswordField("Parola Doğrulama:",validators= [validators.DataRequired(message="Boş Bırakılamaz."),validators.EqualTo(fieldname = "password",message="Doğrulama parolanız, parolanızla uyuşmuyor.")])

# Kullanıcı Login Formu

class LoginForm(Form): # İçerideki Form WTF Formdan alınıyor.
    username = StringField("Kullanıcı Adı",validators=[validators.Length(max=35,min=5,message="Min = 5 / Max = 35 uzunluğunda olmalıdır."),validators.DataRequired(message = "Boş Bırakılamaz.")])
    password = PasswordField("Parola:",validators = [validators.DataRequired(message="Boş Bırakılamaz.")])
# render field'i alabilmek için yani formun oluşması için(renderi için) formhelpers deki render field gerekli ondan login html ye include - import ediyoruz.
# render'de yapılacak olanları(username,password) login html de render methodunu oluşturuyoruz.

app = Flask(__name__)

app.secret_key = "ckblog" # Flash Message Kullanabilmek İçin Gerekli Olan Key

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] ="root"
app.config["MYSQL_PASSWORD"] =""
app.config["MYSQL_DB"] ="ckblog"
app.config["MYSQL_CURSORCLASS"] ="DictCursor" # Mysqldeki veriler liste halinde alınır ve listedeki her eleman sözlük olacak şekilde kodlanır.

mysql = MySQL(app)



@app.route("/")
def index():
    # articles = [ # Liste içierisinde dictionary yapıları bunları htmlde databaseden veri çekerken hep bu şekilde gelecek.
    #     {"Id":1,"Title":"Deneme 1","Content":"Deneme1's Content"}, 
    #     {"Id":2,"Title":"Deneme 2","Content":"Deneme2's Content"},
    #     {"Id":3,"Title":"Deneme 3","Content":"Deneme3's Content"}
    #     ]
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard")
@login_required # Decorator'u decorator'ın altına yazarak (oluşturacağımız decoratoru sadece 1 kere yazarak) herhangi bir fonksiyonda istediğimiz gibi çağırabiliriz.
def dashboard(): # İlk olarak bizim oluşturduğumuz kontrol decoratorundan olumlu sonuçla çıkarsa bu fonksiyon aynı şekilde çağırılır.
    
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * From articles where author = %s"
    
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles) # Alınan article'lar render_template yapısıyla dashboard'a gönderilir.
    else:
        return render_template("dashboard.html") 


@app.route("/article/<string:id>") # url de /article/50 yazdığımızda gidebilmesi için url fonksiyonu yapacağız. Yazılan id'yi stringe çevirip kullanma.
def article(id): # id yi buraya parametre olarak yolluyoruz. Bu şekilde dinamik url yapısı oluşmuş oluyor.
    
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,)) 
    if result > 0:
        article = cursor.fetchone() # Tek bir article alınacağı için çünkü id tek bir id olacak (databasede id (primary key) olarak tasarlandığı için)
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")
 


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles"
    result = cursor.execute(sorgu) 
    if result > 0:
        articles = cursor.fetchall() # Tüm bilgiler (tüm satırlar) databaseden alınır. (Tüm makaleler alınır / fetchone methodu tek makale alır.)
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")





#Register   
@app.route("/register", methods = ["GET","POST"]) # URL'NİN GET VE POST REQUEST ALABİLECEĞİNİ GOSTEREN KOD
# GET ALINAN, POST SUBMIT EDILDIKTEN SONRA GELEN REQUEST URL KOMUTU
def register():
    form = RegisterForm(request.form) # Sayfaya bir request atılmışsa ve bu request post ise formun içindeki tüm bilgiler register formun içine yerleşecek.

    if request.method == "POST" and form.validate(): # Formun gösterileceği yerin kodu submit edildiği zaman (REQUEST POST ISE) / form.validate formda bir sıkıntı yok ise tüm veriler validate kurallarına uyarsa işlemi gerçekleştirir.
        
        name = form.name.data # Formdaki name değişkenin içindeki veriyi alır
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) # Form password değişkeninin içinden alınan veriyi şifreleyerek database'e kaydetmesi için sha256_crypt.encrypt(veri) kullanılır.

        cursor = mysql.connection.cursor() # İmleç görevi database içerisinde hareket edebilmek, veri ekleyip çıkarabilmek için gerekli.
        
        sorgu = "INSERT INTO users(name,username,email,password) VALUES (%s,%s,%s,%s)" # Format methodu da kullanılabilir sqllite'teki ?,?,?,? yapı gibi, veriyi %s kullanarak girilen boşluğa ekler.
        cursor.execute(sorgu,(name,username,email,password)) # Sorgu demet şeklinde alınması gerekmektedir ve tek veri alacaksanız (1.veri,) şeklinde kullanılır.
        # veya tek kodla cursor.execute("INSERT INTO users (name,username,email,password) VALUES (%s,%s,%s,%s)",(name,username,email,password)) şeklinde de kullanılabilir.
        
        mysql.connection.commit() # Database de silme guncelleme ekleme gibi işlem yapılan durumlarda commit kullanılması gerekmektedir yoksa sorgu çalışmaz. İşlem yapılmayan durumlarda(veri çekme gibi) kullanılmasına gerek yoktur.

        cursor.close() # Şart değildir ancak performansı arttırmak açısından database bağlantısını işlem bittikten sonra kesmek faydalıdır.

        flash("Başarıyla Kayıt Oldunuz.","success")
        

        return redirect(url_for("login")) # login adlı fonksiyonun urlsine direk bir şekilde gider.
    else:
        return render_template("register.html",form = form) # Oluşturulan form register html'e gönderilmesi için / Sonra makro oluştur (formhelpers.html)

#Login
@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form) # Formu Login form olarak isimlendirip request classından form nesnesini kullanarak nesne oluşturuyoruz. (form)
 
    if request.method == "POST":

        username = form.username.data
        password_entered =  form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone() #  Tek satıra ait kullanıcının tüm bilgileri databaseden alınır (username,password,email,...) Bunun üzerinde sözlükte gezildiği gibi gezilebilir.
            real_password = data["password"]  # Cursor sorgusu yaptığımızda (kullanıcı adına göre) result > 0 olduğunda yani forma girilen username db var ise o kullanıcının şifresini db'den alıyoruz.
            
            if sha256_crypt.verify(password_entered,real_password): # db'deki şifre ile girilen formdaki şifreyi verify ediyor(doğrulamış oluyor) (yani şifreler uyuşmuş oluyor)
                flash("Başarıyla Giriş Yapıldı.","success") 

                session["logged_in"] = True # Session değişkeni oturum kontrolünde kullanılır,dictionary kullanımıyla aynı yapıya sahiptir. İçerisine anahtar kelime yazılır.
                session["username"] = username


                return redirect(url_for("index"))
            
            else: # şifreler uyuşmamış ise
                flash("Parolanızı Yanlış Girdiniz.","danger") 
                return redirect(url_for("login"))    
        
        else:
            flash("Böyle bir kullanıcı bulunmamaktadır.","danger")
            return redirect(url_for("login"))   



    return render_template("login.html",form = form) # form = form -> formu gönderme işlemi

# Logout
@app.route("/logout")
def logout():
    session.clear() # session'i silerek içerisindeki true değeri kaldırmış oluyoruz ki tekrar giriş yapıldığında döngüde session değeri true olabilsin.
    return redirect(url_for("index"))


# Makale Ekleme

@app.route("/addarticle", methods = ["GET","POST"])
@login_required # Giriş Yapmadan CRUD işlemlerine giriş yapmaya çalışanlar için engel
def addarticle():
    
    form = ArticleForm(request.form) # Oluşturduğumuz classtan request.form nesnesi ile form verisini alarak bir nesne oluşturuyoruz. (form)
    
    if request.method == "POST" and form.validate(): # hem post olması hem de validatelerde sorun olmadığı zaman çalışacak koşul
        title = form.title.data
        content = form.content.data
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES (%s,%s,%s)"
        # username bilgisini sessiondan alacağız.(Author olarak kullanmak için)
        cursor.execute(sorgu,(title,session["username"],content)) # author kullanıcının kendisi olacağından username'i sessiondan aldık.
        
        mysql.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi.","success")

        return redirect(url_for("dashboard"))

    # REQUEST GET OLDUĞUNDA (POST OLMADIĞINDA) AŞAĞIDAKİ GERCEKLEŞİR.
    return render_template("addarticle.html",form = form) # oluşturduğumuz form nesnesi html'e yolluyoruz.

# Makale Silme

@app.route("/delete/<string:id>")
@login_required # Giriş Yapmadan CRUD işlemlerine giriş yapmaya çalışanlar için engel
def delete(id):
    cursor= mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s" # Hem bu id sahip bir article var mı hemde bu article'ın kullanıcısı kendisi olup olmadığını kontrol etmek için 2 sorgu

    result = cursor.execute(sorgu,(session["username"],id)) # yukarıdaki sorguya göre ya 1 ya da 0 döner ve aşağıdaki if koşuluna girer.

    if result > 0:

        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit() # delete işlemi yapıldığından dolayı bağlantı commit edilmeli
        return redirect(url_for("dashboard"))

    else:

        flash("Böyle bir makale bulunmamaktadır veya bu işlemi gerçekleştirmek için izniniz bulunmamaktadır.","danger")
        return redirect(url_for("index"))

# Makale Güncelle

@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required # Giriş Yapmadan CRUD işlemlerine giriş yapmaya çalışanlar için engel
def update(id):

    if request.method == "GET":  # İlk olarak güncelleyebilmek için verinin var olması lazım (yani get ile veriyi alıyoruz)

        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles where id = %s and author = %s" # 2 adet where kullanılmaz where bir kere yazılması başka bir sorgu olmayana kadar yeterlidir.
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:

            flash("Böyle bir makale bulunmamaktadır veya bu işlemi gerçekleştirmek için izniniz bulunmamaktadır.","danger")

            return redirect(url_for("index"))

        else:

            article = cursor.fetchone()
            form = ArticleForm()  # requestten form verilerini alarak nesne oluşturmuyoruz(yani article'dan form verilerini alarak nesne oluşturuyoruz) 

            form.title.data = article["title"] # article form değişkenlerinin içindeki veriyi article verileriyle eşleştiriyoruz.
            form.content.data = article["content"]

            return render_template("update.html",form = form) # verileri eklediğimiz formu rendere yolluyoruz. (form = form ile)

    else:
        # Post Request
        form = ArticleForm(request.form) # submit ederken ArticleForm sınıfından aldığımız formun içine request.form nesnesi ile form verisini alarak bir nesne oluşturuyoruz.

        newTitle = form.title.data  # Yeni oluşturduğumuz form nesnesinin içine article verilerini atıp sonra da onu bir değişkene atıyoruz.
        newContent = form.content.data

        cursor = mysql.connection.cursor()

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s " 

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi.","success")
        return redirect(url_for("dashboard"))

#Makale Form

class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators = [validators.length(min = 5,max = 100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.length(min = 10)]) # Makale Alanı büyük olması gerektiğinden TextAreaField kullandık. Daha rahat daha profesyonel.
    # HTML kodunda textarea verdiğin isim (content) -> textarea class="form-control" id="content" minlength="10" name="content" id ve name'e otomatik olarak atanır.
# Textarea'ları daha rahat ve profesyonel şekilde kullanmak için CKEditor 4 kullanabilirsiniz.


# Arama URL
@app.route("/search",methods = ["GET","POST"])
def search(): 

    if request.method == "GET": # Eğer biri url yerinden search yazarak ulaşmaya çalışırsa direk anasayfaya döndürüyoruz.
        
        return redirect(url_for("index"))

    else:

        keyword = request.form.get("keyword") # Bir post request yapılmışsa ve bu alınmak isteniyorsa
# Amaç : requestin içerisinde form diye bir değişken var ve bunun içindeki get methoduyla ismini keyword olarak atadığımız input alanının içerisindeki veriyi keyword adlı bir değişkene atayarak article'ı bulma
# Text alanının içine ne girilirse o veri keyword olacak.

        cursor = mysql.connection.cursor()

        sorgu = "Select* from articles where title like '%"+ keyword +"%'"  # https://www.w3schools.com/sql/sql_like.asp
        result = cursor.execute(sorgu)

        if result == 0:
            
            flash("Aranan kelimeye uygun makale bulunamadı.","warning")

            return redirect(url_for("articles"))

        else:

            articles = cursor.fetchall() # Yukarıdaki sorgunun sonucuna uygun olan tüm articleri aşağıdaki kodla html'e gönderiyoruz.
            
            # Aranan kelimeye göre sonuç bulundu, filtre felan bunları öğren (list,grid/searchable,sortable HTML table)

            return render_template("articles.html",articles = articles)


if __name__ == "__main__":
    app.run(debug=True) 
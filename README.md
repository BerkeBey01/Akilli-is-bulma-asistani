# Yapay Zeka Destekli İş Arama ve CV Analiz Asistanı

Bu proje, iş arama sürecini otomatize eden, adayların özgeçmişlerini (CV) analiz ederek internetteki en uygun iş ilanlarını bulan ve bu ilanları Yapay Zeka ile skorlayan akıllı bir web uygulamasıdır.

## Proje Hakkında

Geleneksel iş arama yöntemlerinde adaylar binlerce ilanı manuel olarak taramak ve okumak zorundadır. Bu proje, **"Kişisel İK Asistanı"** mantığıyla çalışarak bu süreci tersine çevirir. 

Sistem şu üç temel sorunu çözer:
1.  **CV Analizi:** Yüklenen PDF/DOCX dosyalarından yetenekleri ve deneyimleri otomatik ayrıştırır.
2.  **Otomatik Arama:** Adayın yeteneklerine uygun iş ilanlarını LinkedIn, Indeed ve yerel kaynaklardan (Kariyer.net vb.) otomatik olarak toplar.
3.  **Akıllı Eşleşme:** Bulunan ilanı ve adayın CV'sini anlamsal olarak karşılaştırır, 0-100 arası bir uyum puanı ve geliştirme tavsiyeleri verir.

## Özellikler

*** CV Parsing (Ayrıştırma):** PDF ve Word dosyalarını okuyarak yetenek, deneyim ve eğitim bilgilerini yapısal veriye (JSON) dönüştürür.
*** Meta-Search Motoru:** DuckDuckGo ve Scraping algoritmaları ile birden fazla kaynaktan eş zamanlı iş ilanı taraması yapar.
*** AI Tabanlı Skorlama:** Google Gemini (LLM) kullanarak ilanı ve CV'yi analiz eder; "Teknik", "Deneyim" ve "Eğitim" bazlı detaylı puanlama yapar.
*** Paralel İşleme:** Çoklu ilan analizlerinde performans kaybını önlemek için ThreadPool mimarisi kullanır.
*** Kullanıcı Paneli:** Bulunan ilanların listelendiği, analiz edildiği ve filtrelendiği yönetim paneli.

## Kullanılan Teknolojiler

* **Backend:** Python 3.x, Flask
* **Veritabanı:** SQLite, SQLAlchemy ORM
* **Yapay Zeka:** Google Gemini API (Generative AI)
* **Veri Kazıma:** BeautifulSoup4, DuckDuckGo Search, Requests
* **Dosya İşleme:** PyMuPDF (PDF), python-docx (DOCX)
* **Frontend:** HTML5, CSS3, Bootstrap 5

## Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:
```
### 1. Projeyi Klonlayın
``` bash
git clone https://github.com/BerkeBey01/Akilli-is-bulma-asistani.git
cd Akilli-is-bulma-asistani

### 2. Sanal Ortam (Virtual Environment) Oluşturun
# Windows için
python -m venv venv
venv\Scripts\activate

# Mac/Linux için
python3 -m venv venv
source venv/bin/activate

### 3. Gerekli Kütüphaneleri Yükleyin
pip install -r requirements.txt

### 4. Ortam Değişkenlerini (.env) Ayarlayın
GEMINI_API_KEY=AIzaSyDxxxxxxxxx...
SECRET_KEY=gizli-anahtarim
FLASK_DEBUG=True

### 5. Uygulamayı Başlatın
python app.py

Tarayıcınızda http://127.0.0.1:5000 adresine giderek uygulamayı kullanabilirsiniz.


Nasıl Kullanılır?
Kayıt Ol: Sisteme e-posta ve şifrenizle kayıt olun.

CV Yükle: "CV İşlemleri" menüsünden güncel özgeçmişinizi (PDF/DOCX) yükleyin.

İş Ara: "İş Ara" menüsüne gelin, yüklediğiniz CV'yi seçin ve "İş Ara" butonuna basın.

Analiz Et: "Kaydedilenler" sayfasında bulunan ilanları görüntüleyin. "Analiz Et" butonuna basarak Yapay Zekanın sizin için oluşturduğu uyumluluk raporunu inceleyin.
```
Bu proje, İskenderun Teknik Üniversitesi (İSTE), Bilgisayar Mühendisliği Bölümü, 2024-2025 Eğitim-Öğretim Yılı Mühendislikte Bilgisayar Uygulamaları dersi kapsamında geliştirilmiştir.

import fitz
import docx
import os
import json
import requests
import time
import re
import logging
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from dotenv import load_dotenv

# .env dosyasini yukle
load_dotenv()

# API anahtarini environment variable'dan al
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    logging.warning("GEMINI_API_KEY environment variable bulunamadi!")

# Logging yapilandirmasi
logger = logging.getLogger(__name__)

def _gemini_istegi_gonder(icerik, talimat, sema, temperature=0.3):
    modeller = [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite"
    ]

    payload = {
        "systemInstruction": {"parts": [{"text": talimat}]},
        "contents": [{"parts": [{"text": icerik}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": sema,
            "temperature": temperature
        }
    }

    son_hata = ""

    for model in modeller:
        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            
            if response.status_code == 200:
                raw_text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
                if "```json" in raw_text:
                    raw_text = raw_text.replace("```json", "").replace("```", "")
                elif "```" in raw_text:
                    raw_text = raw_text.replace("```", "")
                return json.loads(raw_text.strip()), None
            else:
                hata_detay = response.json().get('error', {}).get('message', response.text[:200])
                son_hata = f"{model} Hatası: {response.status_code} - {hata_detay}"
                logger.warning(son_hata)
                continue
        except Exception as e:
            son_hata = str(e)
            continue
    
    return None, f"Yapay zeka yanıt vermedi. Son Hata: {son_hata}"

def metin_cikar(dosya_yolu):
    try:
        uzanti = os.path.splitext(dosya_yolu)[1].lower()
        metin = ""
        if uzanti == '.pdf':
            with fitz.open(dosya_yolu) as pdf:
                for sayfa in pdf: metin += sayfa.get_text()
        elif uzanti == '.docx':
            doc = docx.Document(dosya_yolu)
            for p in doc.paragraphs: metin += p.text + "\n"
        return metin, None
    except Exception as e:
        return None, str(e)

def bilgileri_cikar(metin):
    istenen_json_semasi = {
        "type": "OBJECT",
        "properties": {
            "isimler": {"type": "ARRAY", "items": {"type": "STRING"}},
            "epostalar": {"type": "ARRAY", "items": {"type": "STRING"}},
            "telefon_numaralari": {"type": "ARRAY", "items": {"type": "STRING"}},
            "lokasyonlar": {"type": "ARRAY", "items": {"type": "STRING"}},
            "yetenekler": {"type": "ARRAY", "items": {"type": "STRING"}},
            "egitim_bilgileri": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "okul_adi": {"type": "STRING"},
                "bolum_adi": {"type": "STRING"},
                "derece": {"type": "STRING"},
                "mezuniyet_yili": {"type": "STRING"}
            }}},
            "is_deneyimleri": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "sirket_adi": {"type": "STRING"},
                "pozisyon": {"type": "STRING"},
                "baslangic_tarihi": {"type": "STRING"},
                "bitis_tarihi": {"type": "STRING"},
                "sorumluluklar": {"type": "ARRAY", "items": {"type": "STRING"}}
            }}},
            "yabanci_diller": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "dil": {"type": "STRING"},
                "seviye": {"type": "STRING"}
            }}},
            "sertifikalar": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "sertifika_adi": {"type": "STRING"},
                "kurum": {"type": "STRING"},
                "tarih": {"type": "STRING"}
            }}},
            "projeler": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "proje_adi": {"type": "STRING"},
                "aciklama": {"type": "STRING"},
                "teknolojiler": {"type": "ARRAY", "items": {"type": "STRING"}}
            }}},
            "toplam_deneyim_yili": {"type": "STRING"},
            "ozet": {"type": "STRING"}
        }
    }
    talimat = """Sen deneyimli bir İK asistanısın. CV metnini detaylı analiz et ve JSON formatında çıkar.

Önemli kurallar:
- Yetenekler: Teknik beceriler, yazılım dilleri, frameworkler, araçlar, soft skills hepsini ayrı ayrı listele
- Yabancı diller: Dil adı ve seviyesini (Başlangıç/Orta/İleri/Ana dil) belirt
- İş deneyimleri: Tarihler, pozisyon ve sorumlulukları detaylı çıkar
- Toplam deneyim yılı: İş deneyimlerinden hesapla (örn: "3 yıl")
- Özet: Adayın profilini 2-3 cümleyle özetle
- Sertifikalar: Varsa tüm sertifikaları, kursları, eğitimleri ekle
- Projeler: Kişisel veya iş projelerini ve kullanılan teknolojileri çıkar"""

    return _gemini_istegi_gonder(metin, talimat, istenen_json_semasi)

def url_den_ilan_cek(url):
    try:
        if not url.startswith('http'): url = 'https://' + url
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200: return None, "Siteye erişilemedi."

        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]): script.decompose()
        
        metin = soup.get_text(separator=' ', strip=True)[:15000]
        if len(metin) < 100: return None, "İçerik boş."
        return metin, None
    except Exception as e:
        return None, str(e)

def ilani_karsilastir(cv_verisi, ilan_metni):
    if not ilan_metni or len(ilan_metni) < 50:
        ilan_metni = "İlan içeriğine tam erişilemedi. Başlık ve şirket bilgisine göre genel değerlendirme yap."

    istenen_sonuc_semasi = {
        "type": "OBJECT",
        "properties": {
            "teknik_puan": {"type": "INTEGER"},
            "deneyim_puan": {"type": "INTEGER"},
            "egitim_puan": {"type": "INTEGER"},
            "dil_puan": {"type": "INTEGER"},
            "sertifika_puan": {"type": "INTEGER"},
            "uygunluk_nedeni": {"type": "STRING"},
            "eslesen_yetenekler": {"type": "ARRAY", "items": {"type": "STRING"}},
            "eksik_yetenekler": {"type": "ARRAY", "items": {"type": "STRING"}},
            "deneyim_uyumu": {"type": "STRING"},
            "egitim_uyumu": {"type": "STRING"},
            "dil_uyumu": {"type": "STRING"},
            "guclu_yonler": {"type": "ARRAY", "items": {"type": "STRING"}},
            "gelistirilmesi_gerekenler": {"type": "ARRAY", "items": {"type": "STRING"}},
            "tavsiyeler": {"type": "ARRAY", "items": {"type": "STRING"}}
        }
    }

    talimat = """Sen deneyimli ve TUTARLI bir İK değerlendirme uzmanısın.
Her kategoriyi 0-100 arasında AYRI AYRI puanla. Yuvarlak sayılar kullanma (73, 67, 82 gibi kesin değerler ver).

PUANLAMA SİSTEMİ (Her kategori 0-100 arası):

1. teknik_puan (0-100): Teknik yetenek eşleşmesi
   - İlanda istenen her teknolojiyi say
   - Adayda bulunanları say
   - Formül: (eslesen / istenen) * 100
   - Benzer teknoloji varsa %50 say (React yerine Vue = 0.5 eşleşme)
   - Örnek: 8 teknoloji isteniyor, 5'i tam eşleşiyor, 2'si benzer = (5 + 1) / 8 * 100 = 75

2. deneyim_puan (0-100): Deneyim yılı uyumu
   - İstenen deneyim ile mevcut deneyimi karşılaştır
   - Formül: min(100, (aday_yil / istenen_yil) * 100)
   - 5 yıl istenip 3 yıl varsa: 3/5 * 100 = 60
   - Fazla deneyim: max 100 (overqualified durumu ayrıca belirt)
   - Deneyim belirtilmemişse: 50 ver

3. egitim_puan (0-100): Eğitim uyumu
   - Bölüm tam uyuyor: 100
   - İlgili bölüm (Yazılım Müh. yerine Bilgisayar Müh.): 85
   - Farklı mühendislik: 60
   - Tamamen farklı alan: 30
   - Eğitim istenmiyor: 80

4. dil_puan (0-100): Yabancı dil uyumu
   - Seviye tam uyuyor: 100
   - Bir seviye düşük: 65
   - İki seviye düşük: 35
   - Dil yok: 0
   - Dil istenmiyorsa: 100

5. sertifika_puan (0-100): Sertifika ve proje uyumu
   - İlgili sertifika sayısına göre puanla
   - Projeler varsa +20 bonus
   - Hiç yoksa: 40 (baseline)

ÖNEMLİ KURALLAR:
- ASLA 70, 75, 80, 85, 90 gibi 5'in katları verme
- 67, 73, 81, 88 gibi kesin rakamlar kullan
- Her değerlendirmede AYNI mantığı uygula
- Eksik bilgi varsa orta değer ver (45-55 arası)"""

    prompt = f"ADAY BİLGİLERİ:\n{json.dumps(cv_verisi, ensure_ascii=False, indent=2)}\n\nİŞ İLANI:\n{ilan_metni}"

    # Düşük temperature ile tutarlı sonuç al
    sonuc, hata = _gemini_istegi_gonder(prompt, talimat, istenen_sonuc_semasi, temperature=0.1)

    if sonuc:
        # Alt puanlardan ağırlıklı ortalama hesapla
        teknik = sonuc.get('teknik_puan', 50)
        deneyim = sonuc.get('deneyim_puan', 50)
        egitim = sonuc.get('egitim_puan', 50)
        dil = sonuc.get('dil_puan', 50)
        sertifika = sonuc.get('sertifika_puan', 50)

        # Ağırlıklı ortalama: Teknik %40, Deneyim %25, Eğitim %15, Dil %10, Sertifika %10
        toplam_puan = (teknik * 0.40) + (deneyim * 0.25) + (egitim * 0.15) + (dil * 0.10) + (sertifika * 0.10)

        # Sonuca hesaplanan puanı ekle
        sonuc['uygunluk_skoru'] = round(toplam_puan)

        # Alt puanları da döndür (frontend'de göstermek için)
        sonuc['alt_puanlar'] = {
            'teknik': teknik,
            'deneyim': deneyim,
            'egitim': egitim,
            'dil': dil,
            'sertifika': sertifika
        }

    return sonuc, hata

def internette_is_ara(yetenekler_listesi):
    """
    CV'deki yeteneklere göre birden fazla kaynaktan iş ilanı arar.
    Kaynaklar: LinkedIn, Indeed, Glassdoor, Arbeitnow, Remotive, Kariyer.net, 
    Eleman.net, SecretCV, Yenibiris, Greenhouse ve daha fazlası.
    """
    if not yetenekler_listesi: 
        yetenekler_listesi = ["Yazılım"]
    
    # İlk 3 yeteneği kullan (daha iyi sonuçlar için)
    ana_yetenekler = []
    for yetenek in yetenekler_listesi[:3]:
        temiz = re.sub(r'\s*\(.*?\)', '', yetenek).strip()
        if len(temiz) >= 2:
            ana_yetenekler.append(temiz)
    
    if not ana_yetenekler:
        ana_yetenekler = ["Developer"]
    
    ana_yetenek = ana_yetenekler[0]
    
    tum_sonuclar = []
    eklenen_linkler = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # ========== 1. LinkedIn ==========
    try:
        logger.info(f"LinkedIn araması başlatılıyor: {ana_yetenek}")
        linkedin_base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        for start_index in [0, 25, 50]:
            params = {'keywords': ana_yetenek, 'location': 'Turkey', 'start': start_index}
            try:
                resp = requests.get(linkedin_base, params=params, headers=headers, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    ilanlar = soup.find_all('li')
                    if not ilanlar: break
                    for ilan in ilanlar:
                        try:
                            baslik = ilan.find('h3', class_='base-search-card__title').get_text(strip=True)
                            link = ilan.find('a', class_='base-card__full-link').get('href').split('?')[0]
                            sirket = ilan.find('h4', class_='base-search-card__subtitle').get_text(strip=True)
                            lokasyon = ilan.find('span', class_='job-search-card__location')
                            lokasyon_text = lokasyon.get_text(strip=True) if lokasyon else "Türkiye"
                            if link not in eklenen_linkler:
                                tum_sonuclar.append({
                                    "baslik": baslik, 
                                    "link": link, 
                                    "sirket": sirket, 
                                    "kaynak": "LinkedIn", 
                                    "aciklama": f"{lokasyon_text}"
                                })
                                eklenen_linkler.add(link)
                        except (AttributeError, TypeError):
                            continue
                    time.sleep(0.5)
            except requests.RequestException as e:
                logger.warning(f"LinkedIn istegi basarisiz: {e}")
                break
        logger.info(f"LinkedIn: {len([s for s in tum_sonuclar if s['kaynak'] == 'LinkedIn'])} ilan bulundu")
    except Exception as e:
        logger.error(f"LinkedIn arama hatasi: {e}")

    # ========== 2. Indeed Türkiye ==========
    try:
        logger.info("Indeed Türkiye araması başlatılıyor")
        indeed_url = f"https://tr.indeed.com/jobs?q={ana_yetenek}&l=T%C3%BCrkiye"
        resp = requests.get(indeed_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            job_cards = soup.find_all('div', class_='job_seen_beacon') or soup.find_all('td', class_='resultContent')
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h2', class_='jobTitle') or card.find('a', {'data-jk': True})
                    if title_elem:
                        baslik = title_elem.get_text(strip=True).replace('new', '').strip()
                        link_elem = card.find('a', href=True)
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href.startswith('/'):
                                link = f"https://tr.indeed.com{href}"
                            else:
                                link = href
                            
                            sirket_elem = card.find('span', {'data-testid': 'company-name'}) or card.find('span', class_='companyName')
                            sirket = sirket_elem.get_text(strip=True) if sirket_elem else "Indeed İlanı"
                            
                            lokasyon_elem = card.find('div', {'data-testid': 'text-location'}) or card.find('div', class_='companyLocation')
                            lokasyon = lokasyon_elem.get_text(strip=True) if lokasyon_elem else ""
                            
                            if link not in eklenen_linkler and 'indeed.com' in link:
                                tum_sonuclar.append({
                                    "baslik": baslik,
                                    "link": link,
                                    "sirket": sirket,
                                    "kaynak": "Indeed",
                                    "aciklama": lokasyon
                                })
                                eklenen_linkler.add(link)
                except Exception:
                    continue
        logger.info(f"Indeed: {len([s for s in tum_sonuclar if s['kaynak'] == 'Indeed'])} ilan bulundu")
    except Exception as e:
        logger.warning(f"Indeed arama hatasi: {e}")

    # ========== 3. Arbeitnow (Remote/Global) ==========
    try:
        logger.info("Arbeitnow araması başlatılıyor")
        arbeit_url = "https://www.arbeitnow.com/api/job-board-api"
        resp = requests.get(arbeit_url, timeout=8)
        if resp.status_code == 200:
            jobs = resp.json().get('data', [])
            for job in jobs[:30]:
                title = job.get('title', '').lower()
                if any(y.lower() in title for y in ana_yetenekler):
                    link = job.get('url', '')
                    if link and link not in eklenen_linkler:
                        tum_sonuclar.append({
                            "baslik": job.get('title'),
                            "link": link,
                            "sirket": job.get('company_name', 'Arbeitnow'),
                            "kaynak": "Arbeitnow",
                            "aciklama": f"{job.get('location', 'Remote')} - {', '.join(job.get('tags', [])[:3])}"
                        })
                        eklenen_linkler.add(link)
        logger.info(f"Arbeitnow: {len([s for s in tum_sonuclar if s['kaynak'] == 'Arbeitnow'])} ilan bulundu")
    except Exception as e:
        logger.warning(f"Arbeitnow arama hatasi: {e}")

    # ========== 4. Remotive (Remote Jobs) ==========
    try:
        logger.info("Remotive araması başlatılıyor")
        resp = requests.get("https://remotive.com/api/remote-jobs?limit=50", timeout=8)
        if resp.status_code == 200:
            for job in resp.json().get('jobs', []):
                title = job.get('title', '').lower()
                if any(y.lower() in title for y in ana_yetenekler) or 'developer' in title or 'engineer' in title:
                    link = job.get('url')
                    if link and link not in eklenen_linkler:
                        tum_sonuclar.append({
                            "baslik": job.get('title'), 
                            "link": link, 
                            "sirket": job.get('company_name'), 
                            "kaynak": "Remotive", 
                            "aciklama": f"Remote - {job.get('candidate_required_location', 'Worldwide')}"
                        })
                        eklenen_linkler.add(link)
        logger.info(f"Remotive: {len([s for s in tum_sonuclar if s['kaynak'] == 'Remotive'])} ilan bulundu")
    except Exception as e:
        logger.warning(f"Remotive API hatasi: {e}")

    # ========== 5. Himalayas (Remote Jobs) ==========
    try:
        logger.info("Himalayas araması başlatılıyor")
        himalayas_url = "https://himalayas.app/jobs/api?limit=30"
        resp = requests.get(himalayas_url, timeout=8)
        if resp.status_code == 200:
            jobs = resp.json().get('jobs', [])
            for job in jobs:
                title = job.get('title', '').lower()
                if any(y.lower() in title for y in ana_yetenekler):
                    link = job.get('applicationLink') or f"https://himalayas.app/jobs/{job.get('slug', '')}"
                    if link and link not in eklenen_linkler:
                        tum_sonuclar.append({
                            "baslik": job.get('title'),
                            "link": link,
                            "sirket": job.get('companyName', 'Himalayas'),
                            "kaynak": "Himalayas",
                            "aciklama": f"Remote - {job.get('locationRestrictions', 'Worldwide')}"
                        })
                        eklenen_linkler.add(link)
        logger.info(f"Himalayas: {len([s for s in tum_sonuclar if s['kaynak'] == 'Himalayas'])} ilan bulundu")
    except Exception as e:
        logger.warning(f"Himalayas arama hatasi: {e}")

    # ========== 6. FindWork.dev (Developer Jobs) ==========
    try:
        logger.info("FindWork.dev araması başlatılıyor")
        findwork_url = "https://findwork.dev/api/jobs/"
        resp = requests.get(findwork_url, headers={'Accept': 'application/json'}, timeout=8)
        if resp.status_code == 200:
            jobs = resp.json().get('results', [])
            for job in jobs[:25]:
                title = job.get('role', '').lower()
                if any(y.lower() in title for y in ana_yetenekler) or any(y.lower() in str(job.get('keywords', [])).lower() for y in ana_yetenekler):
                    link = job.get('url')
                    if link and link not in eklenen_linkler:
                        tum_sonuclar.append({
                            "baslik": job.get('role'),
                            "link": link,
                            "sirket": job.get('company_name', 'FindWork'),
                            "kaynak": "FindWork.dev",
                            "aciklama": f"{job.get('location', 'Remote')} - {', '.join(job.get('keywords', [])[:3])}"
                        })
                        eklenen_linkler.add(link)
        logger.info(f"FindWork.dev: {len([s for s in tum_sonuclar if s['kaynak'] == 'FindWork.dev'])} ilan bulundu")
    except Exception as e:
        logger.warning(f"FindWork.dev arama hatasi: {e}")

    # ========== 7. DuckDuckGo ile Türk Siteleri ==========
    try:
        logger.info("DuckDuckGo ile Türk iş siteleri araması başlatılıyor")
        ddgs = DDGS()
        
        # Genişletilmiş arama sorguları
        ats_sorgulari = [
            f'site:kariyer.net "{ana_yetenek}" iş ilanı',
            f'site:yenibiris.com "{ana_yetenek}"',
            f'site:secretcv.com "{ana_yetenek}"',
            f'site:eleman.net "{ana_yetenek}"',
            f'site:glassdoor.com "{ana_yetenek}" turkey OR türkiye',
            f'site:boards.greenhouse.io "{ana_yetenek}"',
            f'site:jobs.lever.co "{ana_yetenek}"',
            f'site:indeed.com "{ana_yetenek}" türkiye OR istanbul',
            f'site:startupjobs.com "{ana_yetenek}" turkey',
            f'site:wellfound.com "{ana_yetenek}"',
        ]
        
        for sorgu in ats_sorgulari:
            time.sleep(0.8)
            try:
                sonuclar = ddgs.text(sorgu, region='tr-tr', max_results=10, backend='lite')
                if sonuclar:
                    for s in sonuclar:
                        link = s.get('href', '')
                        full_title = s.get('title', '')
                        body = s.get('body', '')

                        baslik = full_title
                        sirket = "İş İlanı"
                        
                        kaynak = "Web"
                        if "kariyer.net" in link: kaynak = "Kariyer.net"
                        elif "yenibiris" in link: kaynak = "Yenibiris"
                        elif "secretcv" in link: kaynak = "SecretCV"
                        elif "eleman.net" in link: kaynak = "Eleman.net"
                        elif "glassdoor" in link: kaynak = "Glassdoor"
                        elif "greenhouse" in link: kaynak = "Greenhouse"
                        elif "lever.co" in link: kaynak = "Lever"
                        elif "indeed" in link: kaynak = "Indeed"
                        elif "startupjobs" in link: kaynak = "StartupJobs"
                        elif "wellfound" in link: kaynak = "Wellfound"
                        elif "workable" in link: kaynak = "Workable"
                        
                        separators = [" - ", " | ", " — ", " at ", " · "]
                        for sep in separators:
                            if sep in full_title:
                                parts = full_title.split(sep)
                                baslik = parts[0].strip()
                                if len(parts) > 1:
                                    sirket = parts[1].strip()
                                break

                        if link and link.startswith('http') and link not in eklenen_linkler:
                            title_lower = full_title.lower()
                            if any(y.lower() in title_lower for y in ana_yetenekler) or \
                               'developer' in title_lower or 'engineer' in title_lower or \
                               'yazılım' in title_lower or 'geliştirici' in title_lower:
                                tum_sonuclar.append({
                                    "baslik": baslik[:100],
                                    "link": link,
                                    "sirket": sirket[:50],
                                    "kaynak": kaynak,
                                    "aciklama": body[:150] if body else ""
                                })
                                eklenen_linkler.add(link)
                                
            except Exception as e:
                logger.debug(f"DuckDuckGo sorgu hatasi ({sorgu[:30]}...): {e}")
                continue
                
        logger.info("DuckDuckGo: Türk sitelerinden arama tamamlandı")
    except Exception as e:
        logger.warning(f"DuckDuckGo arama hatasi: {e}")

    # ========== 8. Bing Search ==========
    try:
        logger.info("Bing arama yapılıyor")
        bing_url = f"https://www.bing.com/search?q={ana_yetenek}+job+turkey+site:linkedin.com+OR+site:indeed.com"
        resp = requests.get(bing_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for result in soup.find_all('li', class_='b_algo')[:10]:
                a_tag = result.find('a', href=True)
                if a_tag:
                    link = a_tag.get('href', '')
                    baslik = a_tag.get_text(strip=True)
                    if link and link not in eklenen_linkler and ('linkedin' in link or 'indeed' in link):
                        sirket = "Bing Search"
                        if 'linkedin' in link: kaynak = "LinkedIn (Bing)"
                        elif 'indeed' in link: kaynak = "Indeed (Bing)"
                        else: kaynak = "Bing"
                        
                        tum_sonuclar.append({
                            "baslik": baslik[:100],
                            "link": link,
                            "sirket": sirket,
                            "kaynak": kaynak,
                            "aciklama": ""
                        })
                        eklenen_linkler.add(link)
    except Exception as e:
        logger.warning(f"Bing arama hatasi: {e}")

    # Sonuçları filtrele
    saglam_sonuclar = [s for s in tum_sonuclar if s['link'].startswith('http')]
    
    # Kaynak bazında özet log
    kaynak_sayilari = {}
    for s in saglam_sonuclar:
        kaynak_sayilari[s['kaynak']] = kaynak_sayilari.get(s['kaynak'], 0) + 1
    
    logger.info(f"Toplam {len(saglam_sonuclar)} ilan bulundu. Kaynak dağılımı: {kaynak_sayilari}")
    
    return saglam_sonuclar, None
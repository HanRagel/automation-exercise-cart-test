"""
Automation Exercise - Ürün Miktarı Doğrulama Testi (Ödev - Grup 2)

Senaryo:
  1. Ana sayfadaki bir ürün için 'View Product' butonuna tıklanır.
  2. Ürün sipariş miktarı 3'e çıkarılır ve ürün sepete eklenir.
  3. Sepet sayfasındaki miktarın sipariş miktarıyla eşleştiği doğrulanır.

Ek kontroller: sepetteki ürün adı, birim fiyat ve toplam fiyat (birim fiyat x miktar).

Çalıştırma:  python urun_miktar_test.py
Sonuçlar ekrana ve sonuc.txt dosyasına yazılır, sepetin ekran görüntüsü sepet.png olarak kaydedilir.
"""
import re
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

# =====================================================================
# AYARLAR
# =====================================================================
URL = "https://automationexercise.com"
URUN_ADI = "Madame Top For Women"   # Test edilecek ürün (ana sayfadaki adıyla)
SIPARIS_MIKTARI = 3                 # Kutuya yazılacak miktar
BEKLENEN_MIKTAR = 3                 # Sepette görülmesi beklenen miktar
                                    # (Testin hata yakalayabildiğini görmek için 4 yapıp çalıştır)

# Reklam sunucuları: bu adreslerden gelen istekler engellenir, böylece
# tam ekran reklamlar tıklamaları kapatamaz.
REKLAM_ADRESLERI = [
    "*googlesyndication.com*", "*doubleclick.net*", "*googleadservices.com*",
    "*adservice.google.com*", "*google-analytics.com*", "*googletagmanager.com*",
    "*fundingchoicesmessages.google.com*",
]

kayitlar = []
kontroller = []   # (kontrol adı, beklenen, gerçekleşen, geçti mi)


def log(metin):
    print(metin)
    kayitlar.append(metin)


# =====================================================================
# TARAYICI
# =====================================================================
driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 15)

# Chrome DevTools Protokolü (CDP) ile reklam adreslerini engelle.
# Bu komutlar sayfa açılmadan ÖNCE verilmeli.
driver.execute_cdp_cmd("Network.enable", {})
driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": REKLAM_ADRESLERI})


# =====================================================================
# YARDIMCI FONKSİYONLAR
# =====================================================================
def guvenli_tikla(eleman):
    """Elemanı ekranın ortasına kaydırıp tıklar. Önünde başka bir şey varsa
    (reklam, çerez penceresi) JavaScript ile tıklar."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", eleman)
    time.sleep(0.5)
    try:
        eleman.click()
    except ElementClickInterceptedException:
        log("  (Uyarı: eleman başka bir öğenin arkasında kaldı, JavaScript ile tıklandı)")
        driver.execute_script("arguments[0].click();", eleman)


def reklami_kapat():
    """Tam ekran reklam açıldıysa adres '#google_vignette' ile biter; sayfa yenilenir."""
    if "google_vignette" in driver.current_url:
        log("  (Uyarı: tam ekran reklam algılandı, sayfa yeniden yükleniyor)")
        driver.get(driver.current_url.split("#")[0])


def cerez_penceresini_kapat():
    """Bazı bölgelerde çıkan çerez onay penceresini, varsa kapatır."""
    try:
        buton = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-cta-consent")))
        buton.click()
        log("  Çerez penceresi kapatıldı")
    except TimeoutException:
        pass   # Pencere çıkmadıysa sorun yok


def fiyat_sayisi(metin):
    """'Rs. 1000' gibi bir metinden 1000 sayısını çıkarır."""
    eslesme = re.search(r"\d+", metin.replace(",", ""))
    return int(eslesme.group()) if eslesme else None


def kontrol(ad, beklenen, gerceklesen):
    gecti = beklenen == gerceklesen
    kontroller.append((ad, beklenen, gerceklesen, gecti))
    durum = "GEÇTİ" if gecti else "BAŞARISIZ"
    log(f"  [{durum}] {ad}: beklenen = {beklenen!r}, gerçekleşen = {gerceklesen!r}")


# =====================================================================
# TEST ADIMLARI
# =====================================================================
try:
    # ---- ADIM 1: Ana sayfa ve 'View Product' ----
    log("ADIM 1: Ana sayfa açılıyor")
    driver.get(URL)
    cerez_penceresini_kapat()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".features_items")))

    # Ürün kartını adına göre bul, içindeki 'View Product' linkini seç
    xpath = (f"//div[contains(@class,'product-image-wrapper')]"
             f"[.//div[contains(@class,'productinfo')]/p[normalize-space()='{URUN_ADI}']]"
             f"//a[contains(normalize-space(),'View Product')]")
    view_product = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    log(f"  '{URUN_ADI}' ürününün 'View Product' butonuna tıklanıyor")
    guvenli_tikla(view_product)
    reklami_kapat()

    # ---- ADIM 2: Ürün sayfasındaki bilgiler ----
    log("\nADIM 2: Ürün detay sayfası")
    wait.until(EC.presence_of_element_located((By.ID, "quantity")))
    sayfa_adi = driver.find_element(By.CSS_SELECTOR, ".product-information h2").text.strip()
    sayfa_fiyati = fiyat_sayisi(driver.find_element(By.CSS_SELECTOR, ".product-information span span").text)
    log(f"  Açılan sayfa: {driver.current_url}")
    log(f"  Ürün adı: {sayfa_adi} | Birim fiyat: Rs. {sayfa_fiyati}")
    kontrol("Doğru ürün sayfası açıldı", URUN_ADI, sayfa_adi)

    # ---- ADIM 3: Miktarı 3 yap ----
    log(f"\nADIM 3: Miktar {SIPARIS_MIKTARI} olarak ayarlanıyor")
    miktar_kutusu = driver.find_element(By.ID, "quantity")
    miktar_kutusu.clear()                       # İçindeki '1' silinir
    miktar_kutusu.send_keys(str(SIPARIS_MIKTARI))
    yazilan = miktar_kutusu.get_attribute("value")
    kontrol("Miktar kutusundaki değer", str(SIPARIS_MIKTARI), yazilan)

    # ---- ADIM 4: Sepete ekle ----
    log("\nADIM 4: 'Add to cart' butonuna tıklanıyor")
    guvenli_tikla(driver.find_element(By.CSS_SELECTOR, "button.cart"))

    # Açılan 'Added!' penceresindeki 'View Cart' linki görünene kadar bekle
    view_cart = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "#cartModal a[href='/view_cart']")))
    log("  'Added!' penceresi açıldı, 'View Cart' linkine tıklanıyor")
    guvenli_tikla(view_cart)
    reklami_kapat()

    # ---- ADIM 5: Sepette doğrula ----
    log("\nADIM 5: Sepet sayfasında doğrulama")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cart_info_table tbody tr")))
    satirlar = driver.find_elements(By.CSS_SELECTOR, "#cart_info_table tbody tr")
    log(f"  Sepetteki ürün satırı sayısı: {len(satirlar)}")
    kontrol("Sepetteki ürün çeşidi sayısı", 1, len(satirlar))

    satir = satirlar[0]
    sepet_adi = satir.find_element(By.CSS_SELECTOR, ".cart_description h4 a").text.strip()
    sepet_fiyati = fiyat_sayisi(satir.find_element(By.CSS_SELECTOR, ".cart_price p").text)
    sepet_miktari = int(satir.find_element(By.CSS_SELECTOR, ".cart_quantity button").text.strip())
    sepet_toplami = fiyat_sayisi(satir.find_element(By.CSS_SELECTOR, ".cart_total_price").text)

    kontrol("Sepetteki miktar (ANA KONTROL)", BEKLENEN_MIKTAR, sepet_miktari)
    kontrol("Sepetteki ürün adı", sayfa_adi, sepet_adi)
    kontrol("Sepetteki birim fiyat", sayfa_fiyati, sepet_fiyati)
    kontrol("Toplam fiyat (birim fiyat x miktar)", sayfa_fiyati * BEKLENEN_MIKTAR, sepet_toplami)

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", satir)
    driver.save_screenshot("sepet.png")
    log("  Sepet ekran görüntüsü kaydedildi: sepet.png")

except Exception as e:
    log(f"\n[TEST ÇALIŞMADI] {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}")
    driver.save_screenshot("hata.png")
    log("  Hata anının ekran görüntüsü kaydedildi: hata.png")
    kontroller.append(("Test akışı", "tamamlanmalı", "yarıda kaldı", False))

finally:
    driver.quit()
    basarisiz = [k for k in kontroller if not k[3]]
    log("\n" + "=" * 60)
    if basarisiz:
        log(f"SONUÇ: TEST BAŞARISIZ ({len(basarisiz)} kontrol tutmadı)")
        for ad, beklenen, gerceklesen, _ in basarisiz:
            log(f"  HATA: {ad} eşleşmiyor. Beklenen {beklenen!r}, gerçekleşen {gerceklesen!r}")
    else:
        log(f"SONUÇ: TEST BAŞARILI (tüm {len(kontroller)} kontrol geçti)")
    log("=" * 60)
    with open("sonuc.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(kayitlar))
    sys.exit(1 if basarisiz else 0)

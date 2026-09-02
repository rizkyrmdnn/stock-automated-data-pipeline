import yfinance as yf


saham = yf.Ticker('GOOGL')
berita_list = saham.news

# check for the news
if len(berita_list) > 0:
    berita_pertama = berita_list[0]
    print("Kunci (keys) yang tersedia di data berita:")
    print(berita_pertama.keys())
    print("\nIsi mentah berita pertama:")
    print(berita_pertama)
else:
    print("Nggak ada berita yang ditarik nih.")

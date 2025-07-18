import requests

"""
SEC (Securities and Exchange Commission) EDGAR class retrieves and parses company 
data from a public JSON file. 
It follows the SEC Fair Access Policy and builds lookup dictionaries to search for a 
company's CIK using either its name or stock ticker. 
The class filters out incomplete entries and provides easy access to company data.
"""
class SecEdgar:
  def __init__(self, fileurl):
    self.fileurl = fileurl
    self.company_name = {}
    self.stock_ticker = {}
    self.cik_data = {}
    
    headers = {'user-agent': 'MLT CB ceina.ellison@gmail.com'}
    r = requests.get(self.fileurl, headers=headers)
    self.filejson = r.json()

    for item in self.filejson.values():
      cik = item.get('cik_str')
      ticker = item.get('ticker')
      name = item.get('title')
      if not name or not ticker: 
        continue
      self.cik_data[cik] = (cik, ticker, name)
      self.company_name[name.lower()] = cik
      self.stock_ticker[ticker.lower()] = cik

  """
  Looks up a company's Central Index Key (CIK) using it's name and
  returns the full company info as a tuple.
  """
  def name_to_cik(self, name):
    cik = self.company_name.get(name.lower())
    if cik:
      return self.cik_data[cik]
    return "Company not found."

  """
  Retrieves the full company info by searching with the company's
  stock ticker symbol.
  """
  def ticker_to_cik(self, ticker):
    cik = self.stock_ticker.get(ticker.lower())
    if cik:
      return self.cik_data[cik]
    return "Ticker not found."
  

url_se = SecEdgar('https://www.sec.gov/files/company_tickers.json')
print(url_se.name_to_cik("Apple Inc."))
print(url_se.ticker_to_cik(""))

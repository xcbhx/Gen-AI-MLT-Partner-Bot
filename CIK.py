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
    
    headers = {'user-agent': 'MLT CE ceina.ellison@gmail.com'}
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
    try: 
      cik = self.company_name[name.lower()]
      return self.cik_data[cik]
    except KeyError:
      return 'Company not found.'

  """
  Retrieves the full company info by searching with the company's
  stock ticker symbol.
  """
  def ticker_to_cik(self, ticker):
    try:
      cik = self.stock_ticker[ticker.lower()]
      return self.cik_data[cik]
    except KeyError:
      return 'Ticker not found.'

  """
  CIKs must be 10 digits (padded with zeros on the left).
  """ 
  def _format_cik(self, cik):
    return str(cik).zfill(10)

  """
  Fetches recent SEC filings for the given CIK from the EDGAR submissions API.
  Returns the 'recent' filings section as a dictionary, which includes arrays of
  accession numbers, primary documents, and descriptions.
  """
  def _get_filings(self, cik):
    headers = {'user-agent': 'MLT CE ceina.ellison@gmail.com'}
    formatted_cik = self._format_cik(cik)
    url = f'https://data.sec.gov/submissions/CIK{formatted_cik}.json'

    try:
      r = requests.get(url, headers=headers)
      r.raise_for_status()
      return r.json()['filings']['recent']
    except:
      raise RuntimeError(f'Failed to fetch filings for CIK {cik}.')

  """
  Fetches all the 10-K reports from selected CIK for given year.
  """
  def annual_filing(self, cik, year):
    try:
      filings = self._get_filings(cik)
    except RuntimeError as e:
      return f'Error {e}'
    
    accession_numbers = filings['accessionNumber']
    primary_docs = filings['primaryDocument']
    descriptions = filings['primaryDocDescription']
    filing_date = filings['filingDate']

    results = []
    for i in range(len(accession_numbers)):
      if descriptions[i] == '10-K' and filing_date[i].startswith(str(year)):
        accession_num = accession_numbers[i].replace('-', '')
        formatted_cik = self._format_cik(cik)
        url = f'https://www.sec.gov/Archives/edgar/data/{formatted_cik}/{accession_num}/{primary_docs[i]}'

        results.append({
          'Filing Date': filing_date[i],
          'Accession Number': accession_numbers[i],
          'Primary Document': primary_docs[i],
          'Description': descriptions[i],
          'Document URL': url
        })
    return results if results else 'No 10-K filing found for the specified year.'

  """
  Fecthes all the 10-Q reports from selected CIK for a given year + quarter.
  """
  def quarterly_filing(self, cik, year, quarter):
    quarter_months = {
      1: [12, 1, 2],
      2: [3, 4, 5],
      3: [6, 7, 8],
      4: [9, 10, 11]
    }

    if quarter not in quarter_months:
      raise ValueError('Quarter must be between 1 and 4.')
    
    try:
      filings = self._get_filings(cik)
    except RuntimeError as e:
      return f'Error {e}'
    
    accession_numbers = filings['accessionNumber']
    primary_docs = filings['primaryDocument']
    descriptions = filings['primaryDocDescription']
    filing_dates = filings['filingDate'] # <-- List of all filing dates

    results = []
    for i in range(len(accession_numbers)):
      description = descriptions[i]
      filing_date = filing_dates[i]

      if description == '10-Q' and filing_date.startswith(str(year)):
        filing_month = int(filing_date.split('-')[1])
        if filing_month in quarter_months[quarter]:
          accession_num = accession_numbers[i].replace('-', '')
          formatted_cik = self._format_cik(cik)
          url = f'https://www.sec.gov/Archives/edgar/data/{formatted_cik}/{accession_num}/{primary_docs[i]}'

          results.append({
            'Filing Date': filing_date,
            'Accession Number': accession_numbers[i],
            'Primary Document': primary_docs[i],
            'Description': description,
            'Document URL': url
          })
    return results if results else 'No 10-Q filing found for the specified year and quarter.'


url_se = SecEdgar('https://www.sec.gov/files/company_tickers.json')
filing_year = 2024
company_info = url_se.name_to_cik('Apple Inc.')
if isinstance(company_info, tuple):
  cik, ticker, name = company_info
  print('\n--- Company Information ---')
  print(f'Company Name: {name}')
  print(f'Stock Ticker: {ticker}')
  print(f'CIK: {url_se._format_cik(cik)}')

  print(f'\n--- {filing_year} 10-K Filing Summary ---') 
  filing_summary = url_se.annual_filing(cik, filing_year)
  print(filing_summary)
else:
  print(company_info)

quarterly = url_se.quarterly_filing(cik, 2024, 2)
print('\n--- 2024 Q2 10-Q Filing(s) ---')
print(quarterly)
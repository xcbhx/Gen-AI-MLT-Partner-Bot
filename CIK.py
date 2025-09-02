import requests
from markdownify import markdownify as md

class SecEdgar:
  def __init__(self, fileurl):
    """
    SEC (Securities and Exchange Commission) EDGAR class retrieves and parses company 
    data from a public JSON file. 
    It follows the SEC Fair Access Policy and builds lookup dictionaries to search for a 
    company's CIK using either its name or stock ticker. 
    """
    self.fileurl = fileurl
    self.company_name = {}
    self.stock_ticker = {}
    self.cik_data = {}
    self.headers = {'user-agent': 'MLT CE ceina.ellison@gmail.com'}

    r = requests.get(self.fileurl, headers=self.headers, timeout=15)
    r.raise_for_status()
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

  def name_to_cik(self, name):
    """
    Looks up a company's Central Index Key (CIK) using it's name and returns the full company info as a tuple.
    """
    try: 
      cik = self.company_name[name.lower()]
      return self.cik_data[cik]
    except KeyError:
      return 'Company not found.'

  def ticker_to_cik(self, ticker):
    """
    Retrieves the full company info by searching with the company's stock ticker symbol.
    """
    try:
      cik = self.stock_ticker[ticker.lower()]
      return self.cik_data[cik]
    except KeyError:
      return 'Ticker not found.'

  def _format_cik(self, cik):
    """
    CIKs must be 10 digits (padded with zeros on the left).
    """ 
    return str(cik).zfill(10)

  def _get_filings(self, cik):
    """
    Fetches recent SEC filings for the given CIK from the EDGAR submissions API.
    """
    formatted_cik = self._format_cik(cik)
    url = f'https://data.sec.gov/submissions/CIK{formatted_cik}.json'

    try:
      r = requests.get(url, headers=self.headers, timeout=15)
      r.raise_for_status()
      return r.json()['filings']['recent']
    except requests.RequestException as e:
      raise RuntimeError(f'Failed to fetch filings for CIK {cik}: {e}')

  def annual_filing(self, cik, year):
    """
    Fetches all the 10-K reports from selected CIK for given year.
    """
    try:
      filings = self._get_filings(cik)
    except RuntimeError as e:
      return f'Error {e}'
    
    accession_numbers = filings['accessionNumber']
    primary_docs = filings['primaryDocument']
    forms = filings['form']
    filing_date = filings['filingDate']

    for i in range(len(accession_numbers)):
      if forms[i] and forms[i].startswith('10-K') and filing_date[i].startswith(str(year)):
        accession_num = accession_numbers[i].replace('-', '')
        clean_cik = str(cik).lstrip('0') or '0' # Avoid empty if cik is '000000000'
        url = f'https://www.sec.gov/Archives/edgar/data/{clean_cik}/{accession_num}/{primary_docs[i]}'
        try:
          response = requests.get(url, headers=self.headers, timeout=15)
          response.raise_for_status()
          return md(response.text)  # Converts HTML into Markdown
        except requests.RequestException as e:
          return f'Failed to fetch filing content: {e}'
    return 'No 10-K filing found for the specified year.'

  def quarterly_filing(self, cik, year, quarter):
    """
    Fecthes all the 10-Q reports from selected CIK for a given year + quarter.
    """
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
    filing_dates = filings['filingDate'] # <-- List of all filing dates
    forms = filings['form']

    for i in range(len(accession_numbers)):
      filing_date = filing_dates[i]

      if forms[i] and forms[i].startswith('10-Q') and filing_date.startswith(str(year)):
        filing_month = int(filing_date.split('-')[1])
        if filing_month in quarter_months[quarter]:
          accession_num = accession_numbers[i].replace('-', '')
          clean_cik = str(cik).lstrip('0') or '0'
          url = f'https://www.sec.gov/Archives/edgar/data/{clean_cik}/{accession_num}/{primary_docs[i]}'
          try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return md(response.text)  # Converts HTML into Markdown
          except requests.RequestException as e:
            return f'Failed to fetch filing content: {e}'
    return 'No 10-Q filing found for the specified year and quarter.'
          
        


url_se = SecEdgar('https://www.sec.gov/files/company_tickers.json')
company_info = url_se.name_to_cik('Apple Inc.')
if isinstance(company_info, tuple):
  cik, ticker, name = company_info
  print('\n--- Company Information ---')
  print(f'Company Name: {name} (Stock Ticker:{ticker})\n')

  print(f'\n---2024 10-K Filing Summary ---') 
  print(url_se.annual_filing(cik, 2024))

  print('\n--- 2024 Q2 10-Q Filing(s) ---')
  print(url_se.quarterly_filing(cik, 2024, 2))
else:
  print(company_info)
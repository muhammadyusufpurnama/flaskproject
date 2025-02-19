from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
import os
import pandas as pd
from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERNAME = os.getenv("SIPNBP_USERNAME", "DISHUT-JATIM")
PASSWORD = os.getenv("SIPNBP_PASSWORD", "!Jatim123!")
BASE_URL = "https://sipnbp.menlhk.go.id/si-pnbp2/"

# Global variable to store the WebDriver instance
driver_instance = None

def get_driver():
    global driver_instance
    if driver_instance is None:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver_instance = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        driver_instance.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
    return driver_instance

def cleanup_driver():
    global driver_instance
    if driver_instance:
        try:
            driver_instance.quit()
        except:
            pass
        finally:
            driver_instance = None

def get_total_pages(driver, wait):
    try:
        pagination_info = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pgui-pagination")))
        page_links = pagination_info.find_elements(By.CSS_SELECTOR, "a[data-page]")
        if page_links:
            page_numbers = [int(link.get_attribute('data-page')) for link in page_links if link.get_attribute('data-page').isdigit()]
            return max(page_numbers) if page_numbers else 1
        return 1
    except Exception as e:
        print(f"❌ Error getting total pages: {e}")
        return 1

def selenium_login_and_goto_bill_tracking(driver):
    driver.get(BASE_URL + "login.php")
    wait = WebDriverWait(driver, 15)
    try:
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        user_input.send_keys(USERNAME)
        pass_input.send_keys(PASSWORD)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()
        time.sleep(3)
    except Exception as e:
        print(f"❌ Gagal login Selenium: {e}")
        return False
    driver.get(BASE_URL + "bill_tracking.php")
    time.sleep(3)
    return True

def check_pagination_status(driver, wait):
    try:
        next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.pgui-pagination-next")))
        prev_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.pgui-pagination-prev")))
        
        has_next = "disabled" not in next_button.get_attribute("class")
        has_previous = "disabled" not in prev_button.get_attribute("class")
        
        return has_next, has_previous
    except Exception as e:
        print(f"❌ Error checking pagination status: {e}")
        return False, False

def scrape_page_data(driver, wait):
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.pg-row")))
        time.sleep(2)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        rows = soup.find_all("tr", class_="pg-row")
        
        # Check pagination status and total pages
        has_next, has_previous = check_pagination_status(driver, wait)
        total_pages = get_total_pages(driver, wait)
        
        session['has_next'] = has_next
        session['has_previous'] = has_previous
        session['total_pages'] = total_pages
        
        data = [extract_data_from_row(row) for row in rows]
        session['current_data'] = data
        return data
    except TimeoutException:
        print("⚠ Timeout menunggu data tabel.")
        return []

def apply_date_filter_selenium(lhp_start_date=None, lhp_end_date=None, perhutani_name=None):
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 30)

        if not selenium_login_and_goto_bill_tracking(driver):
            cleanup_driver()
            return None
        
        if lhp_start_date:
            try:
                filter_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'th[data-field-name="LHP_TGL"] a.column-filter-trigger.js-filter-trigger'))
                )
                filter_button.click()
                time.sleep(2)

                year_str = str(lhp_start_date.year)
                month_str = lhp_start_date.strftime("%b")
                if lhp_end_date is None:
                    day_list = [lhp_start_date.day]
                else:
                    day_list = list(range(lhp_start_date.day, lhp_end_date.day + 1))

                # Expand year
                year_xpath = f"//div[contains(@class,'js-date-tree')]//label[@title='{year_str}']/preceding-sibling::a[contains(@class, 'js-caret')]"
                year_caret = wait.until(EC.element_to_be_clickable((By.XPATH, year_xpath)))
                driver.execute_script("arguments[0].click();", year_caret)
                time.sleep(1)

                # Expand month
                month_xpath = f"//div[contains(@class,'js-date-tree')]//label[@title='{year_str}']/following-sibling::div[contains(@class,'js-children')]//div[contains(@class,'js-group')]//label[@title='{month_str}']/preceding-sibling::a[contains(@class,'js-caret')]"
                month_caret = wait.until(EC.element_to_be_clickable((By.XPATH, month_xpath)))
                driver.execute_script("arguments[0].click();", month_caret)
                time.sleep(1)

                # Select days
                for day in day_list:
                    day_str = str(day)
                    try:
                        day_xpath = f"//div[contains(@class,'js-group')]//label[@title='{month_str}']/following-sibling::div[contains(@class,'js-children') and contains(@style, 'block')]//label[@title='{day_str}']/input[@class='js-toggle-component']"
                        day_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
                        driver.execute_script("arguments[0].click();", day_checkbox)
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"❌ Gagal mencentang tanggal {day_str}: {e}")
                        continue

                # Apply filter
                apply_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-apply.btn.btn-sm.btn-primary"))
                )
                driver.execute_script("arguments[0].click();", apply_button)
                time.sleep(3)

            except Exception as e:
                print(f"❌ Error applying date filter: {str(e)}")
                cleanup_driver()
                return None

        if perhutani_name:
            try:
                quick_filter_input = wait.until(
                    EC.presence_of_element_located((By.NAME, "quick_filter"))
                )
                quick_filter_input.clear()
                quick_filter_input.send_keys(perhutani_name)
                quick_filter_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-submit[title='Search']"))
                )
                driver.execute_script("arguments[0].click();", quick_filter_button)
                time.sleep(3)
            except Exception as e:
                print(f"⚠ Gagal menerapkan quick filter: {e}")

        # Get initial page data
        data = scrape_page_data(driver, wait)
        session['current_page'] = 1
        
        return data

    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        cleanup_driver()
        return None

def parse_date(date_str):
    if not date_str or date_str.strip() == "-":
        return None
    try:
        date_only = " ".join(date_str.strip().split()[:3])
        return datetime.strptime(date_only, "%d %b %Y").date()
    except ValueError as e:
        print(f"❌ Error parsing date: {date_str} -> {e}")
        return None

def extract_data_from_row(tr):
    tds = tr.find_all("td")
    return {
        "TRX ID": tds[3].get_text(strip=True) if len(tds) > 3 else "-",
        "NPWSHUT NO": tds[4].get_text(strip=True) if len(tds) > 4 else "-",
        "Nama Wajib Bayar": tds[5].get_text(separator=" ", strip=True) if len(tds) > 5 else "-",
        "LHP No": tds[6].get_text(strip=True) if len(tds) > 6 else "-",
        "Tanggal LHP": parse_date(tds[7].get_text(strip=True)) if len(tds) > 7 else None,
        "Total Nominal Billing": tds[8].get_text(strip=True).replace("(IDR)", "").strip() if len(tds) > 8 else "-",
        "PNBP KLHK": tds[9].get_text(strip=True) if len(tds) > 9 else "-",
        "Kode Simponi": tds[10].find("a").get_text(strip=True) if len(tds) > 10 and tds[10].find("a") else "-",
        "NTPN": tds[11].find("a").get_text(strip=True) if len(tds) > 11 and tds[11].find("a") else "-",
        "Tanggal Pembayaran": parse_date(tds[12].text.strip()) if len(tds) > 12 else None
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        lhp_start = request.form.get("lhp_start")
        lhp_end = request.form.get("lhp_end")
        payment_start = request.form.get("payment_start")
        payment_end = request.form.get("payment_end")
        perhutani_name = request.form.get("perhutani_name", "").strip()
        max_pages = request.form.get("max_pages", type=int, default=None)

        date_filters = {
            "lhp_start": datetime.strptime(lhp_start, "%Y-%m-%d").date() if lhp_start else None,
            "lhp_end": datetime.strptime(lhp_end, "%Y-%m-%d").date() if lhp_end else None,
            "payment_start": datetime.strptime(payment_start, "%Y-%m-%d").date() if payment_start else None,
            "payment_end": datetime.strptime(payment_end, "%Y-%m-%d").date() if payment_end else None,
            "perhutani_name": perhutani_name.strip() if perhutani_name else None
        }
        
        all_data = apply_date_filter_selenium(
            date_filters["lhp_start"],
            date_filters["lhp_end"],
            perhutani_name
        )
        if not all_data:
            flash("❌ Gagal menerapkan filter via Selenium.", "danger")
            return redirect(url_for("index"))
        return render_template("results.html", data=all_data)
    
    return render_template("index.html")

@app.route("/navigate", methods=["POST"])
def navigate():
    driver = get_driver()
    if not driver:
        flash("❌ Session expired. Please start a new search.", "danger")
        return redirect(url_for("index"))
    
    current_page = session.get('current_page', 1)
    direction = request.form.get('direction')
    
    try:
        wait = WebDriverWait(driver, 30)
        
        if direction == "next":
            next_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.pgui-pagination-next"))
            )
            
            if "disabled" in next_button.get_attribute("class"):
                flash("⚠ No more pages available", "warning")
                return redirect(url_for("results"))
                
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_button)
            session['current_page'] = current_page + 1
            
        elif direction == "previous":
            prev_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.pgui-pagination-prev"))
            )
            
            if "disabled" in prev_button.get_attribute("class"):
                flash("⚠ Already on first page", "warning")
                return redirect(url_for("results"))
                
            driver.execute_script("arguments[0].scrollIntoView(true);", prev_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", prev_button)
            session['current_page'] = current_page - 1
            
        time.sleep(3)
        data = scrape_page_data(driver, wait)
        return render_template("results.html", data=data)
        
    except Exception as e:
        flash(f"❌ Error navigating pages: {str(e)}", "danger")
        cleanup_driver()
        return redirect(url_for("index"))

@app.route("/results")
def results():
    data = session.get('current_data')
    if not data:
        flash("❌ No data available. Please start a new search.", "danger")
        return redirect(url_for("index"))
    return render_template("results.html", data=data)

@app.route("/download_excel")
def download_excel():
    data = session.get('current_data')
    if not data:
        flash("❌ No data available to download.", "danger")
        return redirect(url_for("results"))
    
    try:
        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(data)
        
        # Create an Excel file in memory
        excel_file = BytesIO()
        
        # Write the DataFrame to the Excel file
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='LHP Data', index=False)
            
            # Get the xlsxwriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['LHP Data']
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D3D3D3',
                'border': 1
            })
            
            # Write the column headers with the defined format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Auto-adjust columns' width
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_width)
        
        # Seek to the beginning of the file
        excel_file.seek(0)
        
        # Create the current timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'LHP_Data_{timestamp}.xlsx'
        )
        
    except Exception as e:
        flash(f"❌ Error generating Excel file: {str(e)}", "danger")
        return redirect(url_for("results"))

if __name__ == "__main__":
    app.run(debug=True)
    # Ensure driver is cleaned up when the application exits
    cleanup_driver()
import os
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re

# --- Configurações ---
SHOP_ID = "id" # Seu ID da loja Shopify
SHOPIFY_EMAIL = "email" # SUBSTITUA PELO SEU EMAIL
SHOPIFY_PASSWORD = "senha" # SUBSTITUA PELA SUA SENHA
ESTOQUE_JSON_PATH = os.path.join(os.path.dirname(__file__), "estoque.json")

def get_browser_driver():
    """Initializes and returns a headless Chrome WebDriver."""
    options = Options()
    #options.add_argument("--headless") # Reativar para produção
    #options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Use webdriver_manager to handle driver installation
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_shopify(driver):
    """Realiza o login no Shopify Admin se ainda não estiver logado."""
    print("Iniciando o processo de login único no Shopify...")
    
    # Tenta ir para uma página que certamente exigirá login se não estiver logado
    driver.get(f"https://admin.shopify.com/store/{SHOP_ID}/products")
    wait = WebDriverWait(driver, 15) # Tempo de espera aumentado para carregamento da página de login, achei um bom tempo mediante testes

    try:
        email = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="account_email"]')))
        email.send_keys(SHOPIFY_EMAIL)

        botão_continuar_email = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="account_lookup"]/div[5]/button')))
        botão_continuar_email.click()

        time.sleep(5)
        
        password = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="account_password"]')))
        password.send_keys(SHOPIFY_PASSWORD)

        botao_loguin = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login_form"]/div[2]/div[4]/button')))
        botao_loguin.click()
        
        # Espera por um elemento que só aparece após o login bem-sucedido, por exemplo, o título de produtos
        wait.until(EC.url_contains(f"/store/{SHOP_ID}/products"))
        print("Login realizado com sucesso!")
        return True
    except TimeoutException:
        print("Campo de e-mail ou senha não encontrado após esperar. Assumindo que já está logado ou que a página de login mudou.")
        # Se o elemento 'account_email' não for encontrado, pode ser que já esteja logado.
        # Verificar se o URL é o de produtos para confirmar.
        if f"/store/{SHOP_ID}/products" in driver.current_url:
            print("Já estava logado ou redirecionado para a página de produtos.")
            return True
        else:
            print("Não foi possível logar e não está na página de produtos. Pode haver um problema.")
            return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o login: {e}")
        return False

def stock_maintenance():    
    json_path = r"C:\Users\fulano\Desktop\E-commerce 2\Codigos\estoque.json"
        
    if not os.path.exists(json_path):
        print(f"Erro: O arquivo JSON não foi encontrado: {json_path}")
        #return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for i in data.get('camisas', []):
            # Procura em ligas e regiões
            link_shopify = data.get('camisas',  {"link_shopify"[i]})
            link_fornecedor = data.get('camisas',  {"link_fornecedor"[i]})
            

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao ler ou decodificar o arquivo JSON: {e}")
        #return None
            
    #return None                

def extract_supplier_product_data(driver):
    """Extracts product data from the supplier's website."""
    #driver.get(product_url)
    wait = WebDriverWait(driver, 10)
    
    product_data = {}
    
    # Check size availability
    size_availability = {}
    size_mapping = {'P': 'P', 'M': 'M', 'G': 'G', 'GG': 'GG', '2GG': '2GG', '3GG': '3GG'}
    for size_option, size_name in size_mapping.items():
        try:
            # Find the size element and check its class attribute
            size_element = driver.find_element(By.XPATH, f'//a[@data-option="{size_option}"]')
            if size_element: # Caso os elementos "2GG" e "3GG" não existam, continua a lógica
                is_available = "btn-variant-no-stock" not in size_element.get_attribute("class")
                size_availability[size_name] = is_available
                print(f"Tamanho {size_name} está disponível: {is_available}")
            else:
                continue    
        except NoSuchElementException:
            size_availability[size_name] = False
            print(f"Elemento para o tamanho {size_name} não encontrado.")
    
    product_data['size_availability'] = size_availability

def stock_maintenance(driver, product_data):
    
    if not product_data:
        print("Dados do produto não disponíveis. Pulando a criação no Shopify.")
        return           
    
    wait = WebDriverWait(driver, 10)
    
 # Selecionar todas as variantes - checkboxes - são ids dinâmicos, so we select by a common attribute
    try:
        sizes_list = list(product_data['size_availability'].items())
        print(sizes_list)
        checkboxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[contains(@id, "Select-")]')))
        
        if len(checkboxes) == len(sizes_list):
            for i, (checkbox, (size, is_available)) in enumerate(zip(checkboxes, sizes_list)):
                quantity = 10 if is_available else 0
                
                if not checkbox.is_selected():
                    try:
                        driver.execute_script("arguments[0].click();", checkbox)
                        time.sleep(3) # Increased delay to avoid race conditions and give time for UI to update

                        # Click the options menu (three dots)
                        options_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div[1]/div/div/div[2]/main/div/div/div/div/div[2]/form/div/div[1]/div[5]/div/div[6]/div[1]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/div[1]/div[2]/div/span/button')))
                        
                        # Usando JavaScript para clicar no botão - to bypass interception
                        driver.execute_script("arguments[0].click();", options_button)
                        time.sleep(2)
                        print("Clicou no menu de opções.")

                        # Click "Editar quantidades"
                        edit_quantities_button_xpath = f'//button[.//span[text()="Editar quantidade"]]'
                        edit_quantities_button = wait.until(EC.element_to_be_clickable((By.XPATH, edit_quantities_button_xpath)))
                        edit_quantities_button.click()
                        time.sleep(2)
                        print("Clicou em 'Editar quantidade'.")
                        
                        # Click the 'Rua Curt Hering' option to open the stock editor
                        stock_editor_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[text()="Rua Curt Hering"]')))                    
                        stock_editor_option.click()
                        time.sleep(2)                    
                        print("Abriu o editor de estoque.")

                        # Find the quantity input for each size variant within the modal
                        print(str(quantity))
                        quantity_input_xpath = f'#EditQuantitiesModalApplyToAllField[placeholder="0"][type="number"]'
                        quantity_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, quantity_input_xpath)))
                        quantity_input.clear()
                        quantity_input.send_keys(str(quantity))
                        print(f"Quantidade para {size} definida como {quantity}.")
                        time.sleep(3)

                        # Click "Concluído" in the stock editor modal
                        done_modal_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "Polaris-Modal-Footer")]//button[.//span[text()="Concluído"]]')))                        
                        if done_modal_button:
                            print("achei o botao DONE MODAL BUTTON")
                        driver.execute_script("arguments[0].click();", done_modal_button)                        
                        print("Clicou em 'Concluído' no modal de estoque.")

                        time.sleep(3)
                    except Exception as e:
                        print(f"Erro ao editar o estoque da variante {size}: {e}")
                        break            
        print("Editou o estoque de cada variante com sucesso.")
        
        # Click Save button
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Salvar"]]')))
        save_button.click()
        print("Clicou em 'Salvar'. Produto criado!")
        
        time.sleep(5) # Wait for save to complete

    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"Erro ao criar o produto no Shopify: {e}")

                    
def main():
    driver = None
    try:
        print("Iniciando o navegador...")
        driver = get_browser_driver()

        if not login_shopify(driver):
            print("Falha no login. Encerrando o script.")
            return            

        # Carregar estoque atual
        estoque_data = ESTOQUE_JSON_PATH
        with open(estoque_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
        
        for camisa in data.get("camisas"[]):
            try:
                                                    
                for i in data.get('camisas', []):
                    # Procura em ligas e regiões
                    link_shopify = data.get('camisas',  {"link_shopify"[i]})
                    link_fornecedor = data.get('camisas',  {"link_fornecedor"[i]})
                    extract_supplier_product_data(link_fornecedor)
                    stock_maintenance(link_shopify) 
                    

            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Erro ao ler ou decodificar o arquivo JSON: {e}")
                #return None
            
                                    

    except Exception as e:
        print(f"Ocorreu um erro inesperado na execução principal: {e}")
    finally:
        if driver:
            print("\n----------------------------------------")
            print("Automação concluída. Fechando o navegador.")
            driver.quit()                    
                    
if __name__ == "__main__":
    main()            

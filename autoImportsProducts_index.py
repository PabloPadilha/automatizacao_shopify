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


def login_shopify(driver):
    
    print("Iniciando o processo de login único no Shopify...")
    # Usar uma URL de login ou uma página interna que redireciona para o login
    driver.get("https://admin.shopify.com/store/seu_id/products/new/")
    wait = WebDriverWait(driver, 10) # Increased wait time

    try:
        email = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="account_email"]')))
        email.send_keys("seu_email")

        botão_continuar_email = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="account_lookup"]/div[5]/button')))
        botão_continuar_email.click()

        time.sleep(5)
        
        password = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="account_password"]')))
        password.send_keys("sua_senha")

        botao_loguin = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login_form"]/div[2]/div[4]/button')))
        botao_loguin.click()
        
        time.sleep(5)              
    
    except TimeoutException:
        print("Campo de e-mail não encontrado. Assumindo que já está logado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o login: {e}")
        return False
        
    return True
    
# Função auxiliar para sanitizar nomes de arquivos/pastas (adicionei ela aqui)
def sanitize_filename(filename):
    """Remove ou substitui caracteres que são inválidos em nomes de arquivos/pastas no Windows."""
    invalid_chars = r'[<>:"/\\|?*]'
    # Substitui caracteres inválidos por underscore. Garante que o nome não termina com '.'
    sanitized = re.sub(invalid_chars, '_', filename).strip().strip('.')
    return sanitized

def upload_shopify_images(driver, image_paths):
    """
    Realiza o upload de imagens para a página de produto do Shopify.
    """
    if not image_paths:
        print("Nenhum caminho de imagem fornecido. Pulando etapa de upload.")
        return True

    print(f"Iniciando upload de {len(image_paths)} imagens...")

    try:
        wait = WebDriverWait(driver, 15)

        # ======================================================================
        # VARIÁVEIS PREENCHIDAS COM O SELETOR CORRETO QUE VOCÊ ENCONTROU
        # ======================================================================

        XPATH_BOTAO_ADICIONAR_MIDIA = None

        # ## SELETOR CORRETO E CONFIRMADO! ##
        XPATH_INPUT_DE_ARQUIVO = "//div[contains(@class, 'Polaris-DropZone')]//input[@type='file']"
        
        XPATH_DA_LISTA_DE_IMAGENS_CARREGADAS = '//div[contains(@class, "Polaris-Thumbnail")]/img'
        
        # ======================================================================
        
        print("Localizando o campo de input de arquivo com o seletor exato...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, XPATH_INPUT_DE_ARQUIVO)))
        
        files_string = '\n'.join(image_paths)
        
        print("Enviando caminhos dos arquivos...")
        file_input.send_keys(files_string)
        
        num_imagens_enviadas = len(image_paths)
        print(f"Aguardando confirmação do upload de {num_imagens_enviadas} imagens (máx. 90 segundos)...")
        
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_elements(By.XPATH, XPATH_DA_LISTA_DE_IMAGENS_CARREGADAS)) >= num_imagens_enviadas
        )
        print("Confirmação recebida! Todas as imagens estão na página.")

        print(">>> Upload de imagens concluído com sucesso!")
        return True

    except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(f"!! Erro durante o processo de upload: {type(e).__name__}. Verifique os seletores ou o estado da página.")
        return False
    except Exception as e:
        print(f"!! Ocorreu um erro inesperado durante o upload: {e}")
        return False

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

def find_league_by_team(team_name):
    """
    Busca o nome de um time no arquivo JSON de ligas e retorna o nome da liga/região.
    """
    json_path = r"C:\Users\fulano\Desktop\E-commerce 2\Codigos\ligas_times.json"
    
    if not os.path.exists(json_path):
        print(f"Erro: O arquivo JSON não foi encontrado: {json_path}")
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for categoria in data.get('ligas_de_futebol', []):
            # Procura em ligas e regiões
            if 'ligas' in categoria:
                for liga in categoria['ligas']:
                    if team_name in liga.get('times', []):
                        return liga['nome_liga']
            
            if 'regioes' in categoria:
                for regiao in categoria['regioes']:
                    if team_name in regiao.get('times', []):
                        return regiao['regiao']
                        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao ler ou decodificar o arquivo JSON: {e}")
        return None
        
    return None


def extract_supplier_product_data(driver):
    """Extracts product data from the supplier's website."""
    #driver.get(product_url)
    wait = WebDriverWait(driver, 10)
    
    product_data = {}
    
    try:
        # Extract product title
        title_element = wait.until(EC.presence_of_element_located((By.XPATH, '//h1[@class="js-product-name mb-3"]')))
        product_data['title'] = title_element.text.strip()
        print(f"Título encontrado: {product_data['title']}")

        title_words = product_data['title'].split()
        if len(title_words) > 1:
            team_name = title_words[1]
            print(f"Possível nome do time extraído: '{team_name}'")
            
            # Chama a função para buscar a liga no JSON
            corresponding_league = find_league_by_team(team_name)
            
            # Armazena o nome da liga nos dados do produto se for encontrado
            product_data['collection_name'] = corresponding_league
            if corresponding_league:
                print(f"Time '{team_name}' encontrado na liga/região: '{corresponding_league}'")
            else:
                print(f"Time '{team_name}' não encontrado no arquivo JSON.")
        else:
            product_data['collection_name'] = None
            print("O título do produto não tem pelo menos duas palavras para extrair o nome do time.")                

        # --- Lógica de Extração e Salvamento de Imagens (VERSÃO CORRIGIDA COM SWIPER E DATA-SRCSET) ---
        try:
            # 1. Preparação da pasta (como antes)
            sanitized_title = sanitize_filename(product_data['title'])
            base_images_folder = r"C:\Users\fulano\Desktop\E-commerce 2\Produtos"
            product_images_folder = os.path.join(base_images_folder, sanitized_title)
            
            os.makedirs(product_images_folder, exist_ok=True)
            print(f"Pasta de imagens garantida em: {product_images_folder}")
            
            product_data['image_folder'] = product_images_folder
            saved_image_paths = []
            image_elements = []

            image_elements = [] # Inicializa a lista
            time.sleep(3)

            # 2. PLANO A: Tenta encontrar a galeria (continua o mesmo)
            print("Procurando por galeria de imagens 'Swiper' (Plano A)...")
            time.sleep(3)
            xpath_A = '//div[@class="swiper-wrapper"]//a[contains(@class, "js-product-thumb")]//img'
            gallery_images = driver.find_elements(By.XPATH, xpath_A)

            # Verifica se a lista de imagens da galeria NÃO está vazia
            if gallery_images:
                print(f"Galeria 'Swiper' encontrada com {len(gallery_images)} imagens.")
                image_elements = gallery_images
            else:
                # 3. PLANO B (REFINADO): Se não encontrou galeria, procurar pela imagem principal no seu contêiner específico.
                print("Nenhuma galeria encontrada. Procurando por imagem principal (Plano B Refinado)...")
                try:
                    # ## NOVO SELETOR PARA IMAGEM ÚNICA ##
                    # Busca pela imagem principal dentro do seu contêiner específico.
                    xpath_B = '//div[@class="product-image"]//img[contains(@class, "product-image-element")]'
                    time.sleep(2)
                    
                    # Usamos find_elements para evitar erro se não encontrar nada
                    main_image_list = driver.find_elements(By.XPATH, xpath_B)
                    
                    if main_image_list:
                        print("Imagem principal única encontrada.")
                        image_elements = main_image_list # A lista conterá 1 elemento
                    else:
                        print("!! Seletor do Plano B não encontrou a imagem principal.")

                except NoSuchElementException:
                    print("!! Não foi possível encontrar nem galeria, nem imagem principal.")

            # 4. Loop de Download (agora corrigido para pegar o 'data-srcset')
            if image_elements:
                print(f"Iniciando download de {len(image_elements)} imagem(ns)...")
                for i, img_element in enumerate(image_elements):
                    try:
                        # PONTO CRÍTICO: Pegamos o 'data-srcset' em vez do 'src'
                        srcset = img_element.get_attribute('data-srcset')
                        
                        if not srcset:
                            print(f"Imagem {i+1} não possui 'data-srcset'. Pulando.")
                            continue

                        # Processar o srcset para pegar a primeira URL (geralmente a de menor resolução, mas serve)
                        first_url_part = srcset.split(',')[0] # Pega "url.jpg 480w"
                        image_url_relative = first_url_part.strip().split(' ')[0] # Pega "url.jpg"

                        # Garantir que a URL tenha o protocolo "https"
                        if image_url_relative.startswith('//'):
                            image_url = 'https:' + image_url_relative
                        else:
                            image_url = image_url_relative
                        
                        print(f"URL da Imagem {i+1}: {image_url}")
                        
                        image_filename = f"imagem_{i+1}.jpg"
                        full_image_path = os.path.join(product_images_folder, image_filename)
                        
                        response = requests.get(image_url, timeout=20)
                        response.raise_for_status()
                        
                        with open(full_image_path, 'wb') as img_file:
                            img_file.write(response.content)
                        
                        print(f"-> Imagem {i+1} salva com sucesso em: {full_image_path}")
                        saved_image_paths.append(full_image_path)

                    except Exception as e:
                        print(f"!! Ocorreu um erro ao processar a imagem {i+1}: {e}")
            
            product_data['saved_image_paths'] = saved_image_paths

        except Exception as e:
            print(f"!! Ocorreu um erro geral e fatal na seção de download de imagens: {e}")
            product_data['saved_image_paths'] = []

        # --- Fim da Lógica de Extração e Salvamento de Imagens ---
        
        # Extract prices
        price_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="price_display"]')))
        # Use a regex to find numbers with comma or dot as decimal separator
        price_match = re.search(r'[\d,\.]+', price_element.text.replace('.', '').replace(',', '.'))
        product_data['price'] = float(price_match.group()) if price_match else 0.0
        print(f"Preço encontrado: R${product_data['price']:.2f}")
        
        try:
            compare_price_element = driver.find_element(By.XPATH, '//*[@id="compare_price_display"]')
            compare_price_match = re.search(r'[\d,\.]+', compare_price_element.text.replace('.', '').replace(',', '.'))
            product_data['compare_price'] = float(compare_price_match.group()) if compare_price_match else None
            print(f"Preço de comparação encontrado: R${product_data['compare_price']:.2f}")
        except NoSuchElementException:
            product_data['compare_price'] = None
            print("Preço de comparação não encontrado.")
            
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
        
    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"Erro ao extrair dados do produto: {e}")
        return None
        
    return product_data

def create_shopify_product(driver, product_data):
    """Creates a new product in Shopify with the extracted data."""
    if not product_data:
        print("Dados do produto não disponíveis. Pulando a criação no Shopify.")
        return           
    
    wait = WebDriverWait(driver, 10)
    
    try:
        print("Preenchendo informações do produto no Shopify...")                            
        
        produtos_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Produtos']/ancestor::a")))
        produtos_link.click()
        print("Clicou no link 'Produtos' na navegação lateral.")
        time.sleep(5) 
        
        add_product_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='Adicionar produto']]")))
        add_product_button.click()
        print("Clicou no botão 'Adicionar produto'.")
        time.sleep(5) # Tempo para a nova página de criação de produto carregar        
        
        found = None # Inicializa para que o loop comece

        while found != True: # Condição que você solicitou
            try:
                # Estas ações precisam ser REPETIDAS a cada tentativa/recarregamento
                add_variant_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Adicionar opções como tamanho ou cor")]')))
                add_variant_button.click()
                print("Clicou em 'Adicionar opções' para ativar o painel de variantes.")
                time.sleep(3)

                # A busca pela variável que controla o loop também precisa ser AQUI
                variant_name_field = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionName[0]"]')))
                if variant_name_field:
                    found = True
                print("Campo 'Nome da opção' encontrado. Prosseguindo com a configuração das variantes.")

            except (TimeoutException, NoSuchElementException) as e:
                # Se não encontrar, ele permanece None, e o loop continua.
                print(f"Campo 'Nome da opção' não encontrado: {e}. Recarregando a página e tentando novamente...")
                driver.get("https://admin.shopify.com/store/seu_id/products/new/")
                time.sleep(5)
            except Exception as e:
                print(f"Ocorreu um erro inesperado durante a tentativa de encontrar o campo de variante: {e}")
                driver.get("https://admin.shopify.com/store/seu_id/products/new/")
                time.sleep(5)          
        
        wait = WebDriverWait(driver, 5) # Increased wait time
        # Fill Title - Using a more stable locator (aria-label)
        title_field = wait.until(EC.presence_of_element_located((By.NAME, 'title')))
        title_field.send_keys(product_data['title'])
        print("Título preenchido.")
        
        print("\n--- Iniciando processo de Mídia ---")
        image_paths = product_data.get('saved_image_paths', [])
        upload_bem_sucedido = upload_shopify_images(driver, image_paths)
        if not upload_bem_sucedido:
            print("AVISO: Houve uma falha no upload das imagens. O script continuará, mas o produto pode ficar sem imagens.")
        
        try:
            iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'product-description_ifr')))
            driver.switch_to.frame(iframe)
            description_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tinymce"]/p')))
            description_field.click()
            description_text = """
            Camisa esportiva respirável com secagem rápida em poliéster.
            
            Benefícios
            • Tecnologia para absorver o suor da sua pele para evaporação mais rápida,
            ajudando a manter você seco e confortável.

            Detalhes do Produto
            • 100% poliéster
            • Lavável à máquina

            Não perca a chance de ter a sua. Junte-se aos atletas.

            As Camisas versão jogador que oferecemos em nossa loja são de uma qualidade excepcional, replicando com fidelidade as camisas usadas pelos jogadores nos gramados. Projetadas para oferecer o máximo conforto e liberdade de movimentos, estas camisas trazem todos os detalhes, cores, escudos e patrocinadores dos uniformes originais. Nossas peças são mais do que apenas réplicas, são uma celebração apaixonada do esporte que amamos.

            TABELA DE MEDIDAS
            TAMANHO    LARGURA    ALTURA
            P          50 cm      69 cm
            M          52 cm      70 cm
            G          54 cm      73 cm
            GG         56 cm      74 cm
            XG         58 cm      76 cm

            *as medidas podem variar 2 a 3 cm para mais ou para menos."""
            description_field.clear()
            description_field.send_keys(description_text)
            time.sleep(4)
            print("Descrição preenchida.")

            driver.switch_to.default_content()

        except Exception as e:
            driver.switch_to.default_content()
            print(f"Ocorreu um erro: {e}")
            
        #upload_image_xpath = f'//*[@id="AppFrameScrollable"]/div/div/div/div[2]/form/div/div[1]/div[1]/div/div/div[2]/div/div[3]/div/div[2]/div/div/div[1]/div[1]/button'        
        
        if 'collection_name' in product_data and product_data['collection_name']:
            print(f"Preenchendo o campo de coleção com: {product_data['collection_name']}")
            # Encontra o campo de coleção (Autocomplete)
            campo_colecao = wait.until(EC.presence_of_element_located((By.ID, 'CollectionsAutocompleteField1')))
            campo_colecao.click()
            campo_colecao.send_keys(product_data['collection_name'])
            time.sleep(1)
            campo_colecao.send_keys(Keys.ENTER)
            campo_colecao.send_keys(Keys.TAB)    
            print(f"Preenchido o campo de coleção!")
                                    
        else:
            print("Não foi possível encontrar uma coleção correspondente no JSON para preencher.")
                        
        # Fill Prices
        shopify_price = (product_data['price'] + (40+20))*1.25
        compare_at_price = shopify_price + 100
        
        print("cheguei até aqui")
        # Using a more stable locator for price fields
        # They have placeholders like "0,00", so let's use that
        price_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="0,00" and @name="price"]')))
        price_field.send_keys(str(shopify_price))
        print("Preço de venda preenchido.")
        
        compare_price_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="0,00" and @name="compareAtPrice"]')))
        compare_price_field.send_keys(str(compare_at_price))
        print("Preço de comparação preenchido.")
        
        cost_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="unitCost"]')))
        cost_field.send_keys(str(product_data['price']))
        print("Custo por item preenchido.")
        
        # Fill Weight
        weight_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="ShippingCardWeight"]')))
        weight_field.clear()
        weight_field.send_keys("150,00")
        print("Peso preenchido.")
        
        # Select weight unit (g)
        # Using a more robust selector
        weight_unit_select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="ShippingCardWeightUnit"]')))
        weight_unit_select = Select(weight_unit_select_element)
        weight_unit_select.select_by_value("GRAMS")
        print("Unidade de peso selecionada para gramas.")
        time.sleep(3)
        
        # Add variants
        #add_variant_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Adicionar opções como tamanho ou cor")]')))
        #add_variant_button.click()
        #print("Clicou em 'Adicionar opções.")
        #time.sleep(3)
        
        # Declare variant titles and values
        variant_name_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionName[0]"]')))
        variant_name_field.send_keys("Tamanho")
        print("Titulo Principal da variante preenchido.")
        time.sleep(1)

        # Find the input fields for variant values based on their role and parent container
        #variant_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[contains(@id, ":r") and @name and not(@name="optionName[0]")]')))
        size_P = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionValue[0][0]"]')))
        size_P.click()
        size_P.send_keys("P")
        size_M = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionValue[0][1]"]')))
        size_M.send_keys("M")
        size_G = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionValue[0][2]"]')))
        size_G.send_keys("G")
        size_GG = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionValue[0][3]"]')))
        size_GG.send_keys("GG")
        size_GG = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionValue[0][4]"]')))
        size_GG.send_keys("2GG")
        size_GG = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.Polaris-TextField__Input[name="optionValue[0][5]"]')))
        size_GG.send_keys("3GG")        
        
        done_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button/span[text()="Concluído"]')))
        done_button.click()
        print("Clicou em 'Concluído' nas variantes.")
        
        time.sleep(2) # Wait for variants to load
        
         # Set variant stock
        # Select all variant checkboxes - The IDs are dynamic, so we select by a common attribute
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
                        
                        # Use JavaScript to click the button to bypass interception
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
        #os.system('cls')

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

        file_path = r"C:\Users\fulano\Desktop\E-commerce 2\Produtos\ProdutosCopiar\link_produtos.txt"
        with open(file_path, 'r') as f:
            product_links = [line.strip() for line in f.readlines() if line.strip()]

        if not product_links:
            print("Nenhum link encontrado no arquivo.")
            return
            
        print(f"\nIniciando automação para {len(product_links)} produtos...")

        for link in product_links:
            print(f"\n----------------------------------------")
            print(f"Processando link do fornecedor: {link}")
            
            try:
                driver.get(link)
                product_data = extract_supplier_product_data(driver)

                if product_data:
                    print("Navegando para a página de criação de produto no Shopify...")
                    driver.get("https://admin.shopify.com/store/seu_id/products/new")
                    create_shopify_product(driver, product_data)
                else:
                    print(f"Não foi possível extrair dados do link: {link}. Pulando...")
                
            except Exception as e:
                print(f"Ocorreu um erro fatal ao processar o link {link}: {e}")
                print("Continuando para o próximo link...")
                continue

    except Exception as e:
        print(f"Ocorreu um erro inesperado na execução principal: {e}")
    finally:
        if driver:
            print("\n----------------------------------------")
            print("Automação concluída. Fechando o navegador.")
            driver.quit()


if __name__ == "__main__":
    main()

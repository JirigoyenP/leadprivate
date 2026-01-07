#Para que funcione en servidor
#!pip install selenium
#!pip install 2captcha-python
#!apt-get update
#!apt-get install firefox #python3 firefox geckodriver
#!pip install beautifulsoup4
#!pip install cloud-sql-python-connector
#!pip install --upgrade sqlalchemy

#para que funcione en computadora
from ast import Try
from ctypes.wintypes import BOOL
import os
from xmlrpc.client import boolean

#Pasar seguridad
from twocaptcha import TwoCaptcha
import requests
#Fechas
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
#Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#Google Cloud
#from google.colab import auth #no deja correr en pc
from google.cloud.sql.connector import Connector
import sqlalchemy
#import sqlalchemy
#Funcionalidades
from bs4 import BeautifulSoup as bs
import time
import sys
class Bot4events(webdriver.Firefox):
  #Creacion del bot
  def __init__(self,driverPath=r"C:\Users\HP\Documents\Lenguaje\python\chromedriver\geckodriver.exe"):
    #set up del web b4events para que funcione en el servidor
    #options = webdriver.FirefoxOptions()
    #Para servidor
    #options.add_argument("--headless")
    #options.add_argument("--no-sandbox")
    #options.add_argument('--disable-dev-shm-usage')  #lo agregue
    
    #super(Bot4events, self).__init__(options=options)
    #Para computadora-#no salgan unas advertencias en el cmd
    self.driverPath = driverPath
    os.environ['PATH'] += self.driverPath
    #options.add_experimental_option('excludeSwitches', ['enable-logging'])
    #invocar el __init__ de la clase padre
    super(Bot4events, self).__init__()
    #Variables
    #Keywords arrays  Local
    self.keywordsId=[0,1,2,3,4,5,6,7,8,9,10,11]
    self.keywordsText=["integracion","agencia","dinamicas", "eventos", "presencial","proveedor","catering","shows","BTL","lanzamiento",\
        "activacion","productoras"]#no le coloque algunas cosas para que no tenga plural ni persona
    
    self.dateToday=datetime.now()#dia de hoy
    self.antiqueMax=self.dateToday-(relativedelta(months=3)) #3 meses
    #nombre de usuario
    self.userName="suarezmateo@gmail.com"
    #contrase�a del usuario
    self.userPassword="Bomboperu123"
    #cantidad de post seleccionados
    self.amountPosts=0
    #control de errores-#guardara el html del error
    self.errorsBadPosts=[]#TODO LOS POSTS (error al seleccionar)
    self.errorsNoDate=[]
    self.errorsBadPost=[]
    self.errorsNoPostText=[]
    self.errorsNoAuthor=[]
    self.errorsNoLink=[]
    self.set_page_load_timeout(30)#espera que la pagina carge

    #Variable de SQL
    self.connector=""#objeto conector
    self.pool=""#contiene el objeto conector ya inicializado y configurado
    self.connectedWithCloud=False#indica si  se consiguió conectar con la base de datos
    self.insertQueriesSet=set() #guarda los insertQueries que se utilizaran
    self.errorsInsertQueries=[]#guarda los insertQueries  que ocasionan error

    
  #Metodos--------------------------------------
  def clearConsole(self):
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
  #Para atributos
  #permite conectar con la base de datos
  """def connectSQL(self):#Para google Collab
    try:
        auth.authenticate_user()
    except Exception as e:
        print(e)
        print("No se autentico al usuario")
        self.connectedWithCloud=False
    else:
        try:#Es por siacaso necesite con nuevas personas
            # Configure gcloud.

            project_id="linkedin-bot-380217"
            !gcloud config set project {project_id}
        except Exception as e:
            print(e)
            print("No configuro el proyecto")
            self.connectedWithCloud=False
        else:
            try:
                # grant Cloud SQL Client role to authenticated user

                current_user = !gcloud auth list --filter=status:ACTIVE --format="value(account)"

                !gcloud projects add-iam-policy-binding {project_id} \
                  --member=user:{current_user[0]} \
                  --role="roles/cloudsql.client"
            except Exception as e:
                print(e)
                print("No se pudo dar un rol al usuario autenticado")
                self.connectedWithCloud=False

            else:
                # enable Cloud SQL Admin API
                !gcloud services enable sqladmin.googleapis.com
                #instala dependencias
                

                !{sys.executable} -m pip install cloud-sql-python-connector["pg8000"] SQLAlchemy==2.0.8 #2.0.2
                region="us-central1"
                instance_name="bot4posts"
                project_id="linkedin-bot-380217"
                INSTANCE_CONNECTION_NAME = f"{project_id}:{region}:{instance_name}" # i.e demo-project:us-central1:demo-instance
                DB_USER="postgres"#no funciono con eventSearcher, no tiene autorizacin
                DB_PASS="ix=kV]OaUMh~>q-E"
                DB_NAME="postgres"
                 # initialize Connector object
                self.connector = Connector()
                try:
                  # function to return the database connection object
                  def getconn():
                      conn = self.connector.connect(
                          INSTANCE_CONNECTION_NAME,
                          "pg8000",
                          user=DB_USER,#sera un usuario con acceso
                          password=DB_PASS,
                          db=DB_NAME
                      )
                      return conn

                  # create connection pool with 'creator' argument to our connection object function
                  self.pool = sqlalchemy.create_engine(
                      "postgresql+pg8000://",
                      creator=getconn,
                  )
                except:
                  print("No funciono...")
                  self.connectedWithCloud=False
                else:
                  #Ya esta todo configurado
                  self.connectedWithCloud=True

      """
  def savePostSQL(self):
      if bool(self.insertQueriesSet):
            if self.connectedWithCloud:#Si esta conectado al servidor
              try:
                  with self.pool.connect() as db_conn:
                     
                      #print("Longitud de queriesList: ",str(len(self.insertQueriesSet)))
                      for i in self.insertQueriesSet:
                          try:
                            # inserta la info a la tabla
                              insert_stmt = sqlalchemy.text(
                                  i
                              )
                              # insert entries into table
                              db_conn.execute(insert_stmt)
                          except:
                              print("Hubo un error con  un query...")
                              self.errorsInsertQueries.append(i)
                      
                      db_conn.commit()#ESTO GUARDA LOS CAMBIOS.
                      self.connector.close()#cierra el conector
              except Exception  as e:
                print(e)
                print("No se consiguio conectar con Google Cloud, revise la conexión a internet")
                print("Se creara un archivo sql local")
                self.connector.close()
                self.savePosts()

            else:
              print("Se creara un archivo sql local")
              self.savePosts()
      else:
        print("No hay post que guardar...")
    
  def savePosts(self):
    if bool(self.insertQueriesSet):#Si se guardaron post, crea el archivo sql
        with open("postsLinkedin.sql","w",encoding="utf-8") as file:
            for i in self.insertQueriesSet:
                file.write(i)
        if bool(self.errorsInsertQueries):#Si hay post que ocasionaron error, se  crea un archivo para averiguar porq
            with open("errorsInsertQueries.sql","w",encoding="utf-8") as file:
                for i in self.errorsInsertQueries:
                    file.write(i)
    else:
        print("No se guardaron posts")
  #Metodos para keywords 
  def usekeywords(self):
      if self.connectedWithCloud:
        try:
            with self.pool.connect() as db_conn:
                # Consigue los keywords id y text
                self.keywordsText=db_conn.execute(
                sqlalchemy.text(
                        """CALL sp_get_keywords_text();"""
                )
                ).fetchall()#devuelve una tupla con las keywords
                
                self.keywordsId=db_conn.execute(
                sqlalchemy.text(
                        """CALL sp_get_keywords_id();"""
                )
                ).fetchall()
                 
                
        except Exception  as e:
            print(e)
            print("No se consiguio conectar con Google Cloud, revise la conexión a internet")
            self.connector.close()
      else:
         print("No está conectado con CloudSQL")
  def addkeywords(self):
    if self.connectedWithCloud:
        try:
            with self.pool.connect() as db_conn:
               
               
                #Permite ver  todo el contenido de la tabla
                db_conn.execute(
                sqlalchemy.text(
                   """
                   SELECT * FROM keywords;
                   """                    
                    ))
                #Pregunta la  palabra keyword a agregar, si escribe SALIR nose agrega nada
                print("La palabra que quiere agregar se usara cuando se realice una busqueda de posts")
                print("Escriba SALIR si es que no quiere agregar palabras")
                print("No ingrese palabras con:  ' o ")
                newKeyword=input("Ingrese la palabra")
                while newKeyword.upper()!="SALIR":
                    
                    insert_stmt = f"CALL sp_add_keywords('{newKeyword}');"
                    # Inserta los  datos
                    db_conn.execute(insert_stmt)
                    db_conn.commit()#ESTO GUARDA LOS CAMBIOS.
                    print("La palabra que quiere agregar se usara cuando se realice una busqueda de posts")
                    print("Escriba SALIR si es que no quiere agregar mas palabras")
                    newKeyword=input("Ingrese la palabra")
        except Exception  as e:
            print(e)
            print("No se consiguio conectar con Google Cloud, revise la conexión a internet")
            self.connector.close()
    else:
        print("No está conectado con CloudSQL")
  def updatekeywords(self):
      if self.connectedWithCloud:
        try:
            with self.pool.connect() as db_conn:
                
                #Permite ver  todo el contenido de la tabla
                db_conn.execute(
                sqlalchemy.text(
                    """
                    SELECT * FROM keywords;
                    """                    
                    ))
                #Info para el usuario
                print("Recuerde que la palabra que quiere modificar debe existir en la tabla")
                print("Procure que este escrita igual que en la tabla")
                #Pregunta la palabra, si escribe SALIR no se modifica nada
                
                print("Escriba SALIR si es que no quiere modificar palabras")
                print("No ingrese palabras con:  ' o ")
                existKeyword=input("Ingrese la palabra a modificar")#pide la palabra a cambiar
                newKeyword=input("Ingrese la nueva palabra")#pide la nueva palabra
                
                while newKeyword.upper()!="SALIR" or existKeyword.upper()!="SALIR":
                    
                    insert_stmt = f"""UPDATE keywords SET keyword_text='{newKeyword}'
                                    WHERE keyword_text='{existKeyword}';
                                    SELECT * FROM keywords;"""
                    # insert entries into table
                    db_conn.execute(insert_stmt)
                    db_conn.commit()#ESTO GUARDA LOS CAMBIOS.
                    #Info para el usuario
                    print("Recuerde que la palabra que quiere modificar debe existir en la tabla")
                    print("Procure que este escrita igual que en la tabla")
                    #Pregunta la palabra, si escribe SALIR no se modifica nada
                    print("Escriba SALIR si es que no quiere modificar mas palabras")
                    print("No ingrese palabras con:  ' y  ")
                    existKeyword=input("Ingrese la palabra a modificar")#pide la palabra a cambiar
                    newKeyword=input("Ingrese la nueva palabra")#pide la nueva palabra
        except Exception  as e:
            print(e)
            print("No se consiguio conectar con Google Cloud, revise la conexión a internet")
            self.connector.close()
      else:
        print("No está conectado con CloudSQL")
  def deletekeywords(self):
    if self.connectedWithCloud:
        try:
            with self.pool.connect() as db_conn:
                
                #Permite ver  todo el contenido de la tabla
                
                #Info para el usuario
                print("Recuerde que la palabra que quiere eliminar debe existir en la tabla")
                print("Procure que este escrita igual que en la tabla")
                #Pregunta la palabra keyword a agregar, si escribe SALIR nose agrega nada
                print("Ingrese la palabra que quiere borrar")
                print("Escriba SALIR si es que no quiere borrar palabras")
                print("No ingrese palabras con:  ' o ")
                deleteKeyword=input("Ingrese la palabra  a borrar")#pide la palabra a cambiar
                
                
                while deleteKeyword.upper()!="SALIR":
                    #Cambia el isDeleted de false a true  y devuelve la palabra borrada
                    insert_stmt=f"""
                        CALL sp_delete_keywords('{deleteKeyword}');
                            
                    """
                    
                    # insert entries into table
                    deletedKeywordText=db_conn.execute(insert_stmt)
                    print("Se borro la keyword "+deletedKeywordText)
                    db_conn.commit()#ESTO GUARDA LOS CAMBIOS.
                    db_conn.execute(
                    sqlalchemy.text(
                       """
                       SELECT * FROM keywords;
                       """                    
                        ))
                    
                    print("Escriba SALIR si es que no quiere borrar mas palabras")
                    print("No ingrese palabras con:  ' y  ")
                    deleteKeyword=input("Ingrese la palabra a borrar")#pide la palabra a cambiar
                    
        except Exception  as e:
            print(e)
            print("No se consiguio conectar con Google Cloud, revise la conexión a internet")
            self.connector.close()
    else:
        print("No está conectado con CloudSQL")

  #Metodos con antiqueMax
  #def modifyAntiqueMax(self)
  
  #Funcionamiento
  #Seguridad
  def enterSecurityCode(self):#Si aparece lode enter codigo del correo
      try:
          resendCodeButton= WebDriverWait(self,20).until(
                            EC.presence_of_element_located((By.ID, "btn-resend-pin"))
          )
          resendCodeButton.click()
          try:
              textBox= WebDriverWait(self,20).until(
                        EC.presence_of_element_located((By.ID, "input__email_verification_pin"))
                        )
              
              
              
              #Esto aparece como en consola
              print("Se envio al correo: 'jobs@ebombo.com' el codigo de verificacion")
              SecurityCode=input("Ingrese el codigo de seguridad enviado al correo del usuario maximo 6 digitos: ")
              while len(SecurityCode)<6:
                  SecurityCode=input("Por favor, ingrese el codigo de seguridad enviado al correo del usuario maximo 6 digitos: ")
                  
              textBox.send_keys(SecurityCode)
              button=self.find_element(By.ID, "email-pin-submit-button")#que se vea mejor el input
              button.click()
          except Exception as noVerificationCode:
              print("noVerificationCode:",noVerificationCode)
      except:
        #Pasar captcha
        self.passFunCaptcha()
             #print("noResendButton: ",noResendButton)
  def modFuncaptcha(self):
      self.get("https://iframe.arkoselabs.com/3117BF26-4762-4F5A-8ED9-A85E69209A46/index.html?data=%7B%22challengeId%22%3A%22AQF4IhQzbfZzoAAAAYZ2JJfg5IHnl7XYmu1rk18wcZwpxiM2EHhGZBT6j_xSWJMk6ak0_uey-d9_-CfGOL0HpYaYC-LWgo5DLA%22%2C%22submissionId%22%3A%22Login%3Ad33d3254-3dd7-49aa-8936-cb3050b32090%22%2C%22flowTreeId%22%3A%22AAX1PX7p1CTHw9qSZmWsEg%3D%3D%22%7D&amp;mkt=es")
      try:
        WebDriverWait(self,30).until(
                        EC.presence_of_element_located((By.ID, "FunCaptcha")))
        
        #captcha.find_element(By.ID, "fc_meta_audio_btn").click()
      except:
            print("No hay captcha")
      else:#FunCaptcha-Token
          #inputCaptcha=captcha.find_element(By.CSS_SELECTOR,"#FunCaptcha-Token")
          getToken="CAMBIOelTOKEN"
          #2Captcha indica el elemento con id=fc-token
          #el id que  encontre FunCaptcha-Token
          
          changeToken=self.execute_script(("return document.getElementById('FunCaptcha-Token');")) #input.setAtrribute('value','ola')"))#.value={}").format(getToken))
          #changeToken=self.execute_script(("return document.getElementsByTagName('input');")) #input.setAtrribute('value','ola')"))#.value={}").format(getToken))
          
          print("porID:1 ",changeToken) 
          javascriptCode="document.getElementById('FunCaptcha-Token').value= '{}';"
          changeToken=self.execute_script(javascriptCode.format(getToken))#me sale q es nulo
          print("porID: ",changeToken)
          changeToken=self.execute_script(("return document.getElementById('FunCaptcha-Token').value;"))
          print("porID: ",changeToken)
          
          #el name que encontre similar al id
          changegtoken=self.execute_script(("document.getElementsByName('fc-token');"))
          print("porName: " , changegtoken)
  def passFunCaptcha(self):
        #self.get("https://iframe.arkoselabs.com/3117BF26-4762-4F5A-8ED9-A85E69209A46/index.html?data=%7B%22challengeId%22%3A%22AQF4IhQzbfZzoAAAAYZ2JJfg5IHnl7XYmu1rk18wcZwpxiM2EHhGZBT6j_xSWJMk6ak0_uey-d9_-CfGOL0HpYaYC-LWgo5DLA%22%2C%22submissionId%22%3A%22Login%3Ad33d3254-3dd7-49aa-8936-cb3050b32090%22%2C%22flowTreeId%22%3A%22AAX1PX7p1CTHw9qSZmWsEg%3D%3D%22%7D&amp;mkt=es")
      
        pk="3117BF26-4762-4F5A-8ED9-A85E69209A46"
        surl="https%3A%2F%2Flinkedin-api.arkoselabs.com"
        url=self.current_url
        isFuncaptcha="https://www.linkedin.com/checkpoint/challenge/"
        #isFuncaptcha=("https://iframe.arkoselabs.com/3117BF26-4762-4F5A-8ED9-A85E69209A46/index.html?data=%7B%22challengeId%22%3A%22AQF4IhQzbfZzoAAAAYZ2JJfg5IHnl7XYmu1rk18wcZwpxiM2EHhGZBT6j_xSWJMk6ak0_uey-d9_-CfGOL0HpYaYC-LWgo5DLA%22%2C%22submissionId%22%3A%22Login%3Ad33d3254-3dd7-49aa-8936-cb3050b32090%22%2C%22flowTreeId%22%3A%22AAX1PX7p1CTHw9qSZmWsEg%3D%3D%22%7D&amp;mkt=es")
        
        if isFuncaptcha in url:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

            api_key = 'a4701a0870dd92d0410ceb0c4b9b6c8a'
            solver = TwoCaptcha(f'{api_key}')
            try:
                result = solver.funcaptcha(sitekey=f'{pk}',
                                    url=f'{url}',
                                    surl=f'{surl}')
                print("result: ",result)#ver si me da la rpta
                id=solver.get_result(id)
                print("id: ",id)
                try:
                    print("verque da el get_Result(): ",solver.get_result())
                except:
                    print("no funciono el get_Result()")
            except Exception as e:
              print("no funciono solver: ",str(e))
              #self.changeToRecent()
            else:
                 print('result: ' + str(result))
                 self.execute_script(("return document.getElementById('FunCaptcha-Token').value=result;"))
                 changeToken=self.execute_script(("return document.getElementById('FunCaptcha-Token').value;"))
                 print("changeToken: ", changeToken)
        #else: 
        #    self.changeToRecent()
            #self.postLinkedin()
  def passFunCaptcha1(self):
    #Las 3 veces que mesalió el funcaptcha tenía el mismo surl pk,supongo que no varía, tmp el surl
    pk="3117BF26-4762-4F5A-8ED9-A85E69209A46"
    surl="https%3A%2F%2Flinkedin-api.arkoselabs.com"
    url=self.current_url
    #varía el token, eso es lo q  debo de reemplazar creo
    
    isFuncaptcha="https://www.linkedin.com/checkpoint/challenge/"
    if isFuncaptcha in url:
        print("ENTRO CAPTCHA")
        try:
         
             WebDriverWait(self,50).until(
                            #EC.presence_of_element_located((By.ID, "FunCaptcha"))#No encuentra el elemento
                            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                            )
                      
            #captcha.find_element(By.ID, "fc_meta_audio_btn").click()
        except:

            print("No encontro la presencia del elemento")
            print("Espere unos minutos para que no aparezca el Funcaptcha")
        else:
            #clickCaptchaButton=captcha.find_element(By.ID,"home_children_button")
            #clickCaptchaButton.click()
            sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
            #url=self.execute_script("return window.location.href")
            print("SI HAY CAPTCHA")
        
            api_key = 'a4701a0870dd92d0410ceb0c4b9b6c8a'
            #solver = TwoCaptcha(api_key)
            try:
                #ejemplo url in.php: 
                #http://2captcha.com/in.php?key=1abc234de56fab7c89012d34e56fa7b8&method=funcaptcha&publickey=12AB34CD-56F7-AB8C-9D01-2EF3456789A0&surl=https://client-api.arkoselabs.com&pageurl=http://mysite.com/page/with/funcaptcha/
                print("solicita solución")
                urlEnvio=f"http://2captcha.com/in.php?key={api_key}&method=funcaptcha&publickey={pk}&surl={surl}&pageurl={url}"
                print(urlEnvio)
                #requests.post(urlEnvio)#Esto recibiría el responde 200
                #idCaptcha
                #print("El id captcha: ",idCaptcha)
                #result = solver.funcaptcha(sitekey=pk,
                #                            url=url,
                #                            surl=surl)  #no probado
               #la rpta seguro va por defecto al servidor especificado, pero creo q puedo pedir la solucion
            except Exception as e:
                  if e=="ERROR_NO_SLOT_AVAILABLE":
                      print("no hay espacio en la cola, volver a la peticion")
                  elif e=="ERROR_ZERO_BALANCE":
                      print("No hay efectivo en la cuenta, comprar mas creditos")
                  elif e=="IP_BANNED":
                      print("La IP fue baneada, esperar 5 minutos")
                  elif  e=="ERROR_BAD_PARAMETERS":
                      print("Los parametros son incorrectos, verificar y corregir los parametros")
                  else:
                      print("Revisar que pudo salir mal")

            else:
                 try:

                     time.sleep(19)
                     urlRecoger=f"http://2captcha.com/res.php?key={api_key}&action=get&id={idCaptcha}"
                     print(urlRecoger)
                     #El token del captchase cambia por este token creo
                     getToken=requests.get(urlRecoger)
                     print("Recogio la solucion")
                     print("El token es: ",getToken)
                     #code = result.get_result(id)
                 except Exception as e:
                     if e=="ERROR_KEY_DOES_NOT_EXIST":
                        print("La key fueincorrecta, corregirla")
                     elif e=="ERROR_WRONG_CAPTCHA_ID":
                         print("El Id del Funcaptcha es incorrecto")
                     elif e=="CAPCHA_NOT_READY" or e=="ERROR_CAPTCHA_UNSOLVABLE":
                        if e=="ERROR_CAPTCHA_UNSOLVABLE":
                            print("No se pudo resolver el Funcaptcha")
                        else:
                            print("El funCaptcha no estaba listo denuevo la resolución")
                        time.sleep(5)
                        try:
                            getToken=requests.get(urlRecoger)
                        except Exception as e:
                            if e=="ERROR_KEY_DOES_NOT_EXIST":
                                print("La key fueincorrecta, corregirla")
                            elif e=="ERROR_WRONG_CAPTCHA_ID":
                                print("El Id del Funcaptcha es incorrecto")
                            elif e=="ERROR_CAPTCHA_UNSOLVABLE":
                                print("El funcaptcha no se pudo resolver")
                            else:
                                print("Averiguar el error: "+e)
                        else:
                            self.execute_script(("document.getElementById('FunCaptcha-Token').value = '{}';").format(getToken))

                     else:
                         print("Averiguar el error: "+e)
                 else:
                     #FunCaptcha-Token
                    self.execute_script(("document.getElementById('FunCaptcha-Token').value = '{}';").format(getToken))
        finally:
           self.linkedinPostsOnFeed()
    else:
        self.linkedinPostsOnFeed()
    #    #pk=3117BF26-4762-4F5A-8ED9-A85E69209A46
    #    #surl=https%3A%2F%2Flinkedin-api.arkoselabs.com
    #pk=3117BF26-4762-4F5A-8ED9-A85E69209A46
    # surl=https%3A%2F%2Flinkedin-api.arkoselabs.com
    #pk=3117BF26-4762-4F5A-8ED9-A85E69209A46&amp
    #surl=https%3A%2F%2Flinkedin-api.arkoselabs.com&amp
    #pk=pk=3117BF26-4762-4F5A-8ED9-A85E69209A46
    #pk=3117BF26-4762-4F5A-8ED9-A85E69209A46
    #surl=https%3A%2F%2Flinkedin-api.arkoselabs.com
    #except Exception as noFunCaptcha:
    #      print("noFunCaptcha: ",noFunCaptcha)
  def clickSkipButton(self):
    #podr�a agregar que salte lo del manage-account
    try: #ya lo quite al marcar el correo como correcto, pero por siacaso lo dejo
    #    #apareci� lo del correo innacesible?
    #    #presiona el boton Saltar 
        skipButton= WebDriverWait(self,20).until(
            EC.presence_of_element_located((By.CLASS_NAME,"secondary-action-new")))
        skipButton.click()
        #self.find_element(By.CLASS_NAME,"secondary-action-new").click()
    except:
        print("No entra a manage-account")
        self.enterSecurityCode()
# Linkedin
  def getUserCountry(self, profileLink):
      #entra al perfil del usuario
      self.get(profileLink)
      #Espera que cargue la informacióndel perfil
      WebDriverWait(self,20).until(
                            EC.presence_of_element_located((By.ID, "profile-content"))
          )
      #codigo de js
      getCountryCode="""
        var profileInfo=document.getElementById('profile-content');
        var insideProfile=profileInfo.getElementsByClassName('scaffold-layout__main')[0];

        var box=insideProfile.getElementsByClassName('ph5')[0];
        var countryText= box.getElementsByClassName('text-body-small inline t-black--light break-words')[0].textContent;
        return countryText;
      """
      countryText=self.execute_script(f'{getCountryCode}')
      return countryText
  def specificSearch(self):
      self.enterLinkedin()#inicia la sesión y pasa los metodos de seguridad
      print("Escriba SALIR si es que no quiere realizar una búsqueda especifica")
      profileLink=input("Ingrese el link del perfil de la persona a buscar: ")
      if "SALIR" in profileLink.upper():
          self.quit()#Cierra la instancia del bot
      while not("linkedin" in profileLink):
        print("Recuerde que debe ser el link del perfil de LinkedIn")
        print("Escriba SALIR si es que no quiere realizar una búsqueda especifica")
        profileLink=input("Ingrese el link del perfil de la persona a buscar: ")
        if "SALIR" in profileLink.upper():
          self.quit()#Cierra la instancia del bot
      #Conseguir el país de la persona buscada
      searchedPersonCountry=  self.getUserCountry(profileLink)
      
      #Entra a la seccion de Actividad
      self.get(profileLink+"/recent-activity/")
      try:
          #Espera que cargue el elemento
          
          infoUser=WebDriverWait(self,20).until(
                            EC.presence_of_element_located((By.ID, "recent-activity-top-card"))
          )
          #Consigue elnombre  de la persona buscada
          divInfoUser=infoUser.find_elements(By.TAG_NAME,"div")[4]
          hText=divInfoUser.find_element(By.TAG_NAME,"h3").text
          searchedPersonName=hText
          #searchedPersonName=self.execute(f'{jsCodeprofileLinkName}')
      except:
          #No encontro el nombre
          searchedPersonName="Anonimo"
      
      try:
          def makingTheSpecificSearching():
              scrollPauseTime= 2
      
              #en el feed se muestran al inicio 10 posts, pero no todos son visibles
              #m�s se baja en el feed, aparecen 5 post +, pero no todos son visibles
              
              print("Informacion: ")
              print("Si fue hace menos de un minuto, especifique la cantidad de segundos como: 30 segundos")
              print("Si fue hace menos de una hora, especifique la cantidad de minutos como: 5 minutos")
              print("Si fue hace menos de un dia, especifique la cantidad de horas como:  5 horas")
              print("Si fue hace menos de un año, especifique la cantidad de meses como:  5 meses")
              print("Si fue hace mas de un año pero menor a 2 años, especifique la cantidad de años como:  1 año")
              print("Si fue hace mas de 2 años pero menor a 3 años, especifique la cantidad de años como:  2 años")
              print("Así con tiempos mayores")
              print("Recuerde:")
              print("La fecha máxima debe ser mayor a la fecha minima")
              print("No pueden ser iguales")
              print("Mientras más antiguo sea el post a buscar, la búsqueda demorara más")
              #pide la fecha máxima
              pastTimeTextMax=input("Ingrese hace cuanto tiempo fue el post (fecha máxima): ")
              #pide la fecha minima
              pastTimeTextMin=input("Ingrese hace cuanto tiempo fue el post (fecha minima): ")
              def getDate(pastTime):
                  try:
                      #transforma el texto en fecha
                      pastTimeList=pastTime.split(" ")  
                      #print(pastTimeList)
                      if "segundo" in pastTimeList[1]:
                            substractDate=(relativedelta(seconds=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      elif "minuto" in pastTimeList[1]:
                            substractDate=(relativedelta(minutes=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      elif "hora" in pastTimeList[1]:
                            substractDate=(relativedelta(hours=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      elif "día" in pastTimeList[1] or "dia" in pastTimeList[1]:
                            substractDate=(relativedelta(days=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      elif "semana" in pastTimeList[1]:
                            substractDate=(relativedelta(weeks=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      elif "mes" in pastTimeList[1]:
                            substractDate=(relativedelta(months=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      elif "año" in pastTimeList[1]:
                            substractDate=(relativedelta(years=int(pastTimeList[0])))
                            #print(substractDate)
                            dateToCompare=(self.dateToday-substractDate)
                      return dateToCompare
                  except:
                      print("Ingrese correctamente la fecha minima y  maxima")
                      print("Vuelva a ejecutar la funcion...")
                      self.quit()
              #obtiene las fechas
              pastTimeMax=getDate(pastTimeTextMax)

              pastTimeMin=getDate(pastTimeTextMin)
              #Ve si la fecha max es mayor a la fecha min
              #La fecha mayor es la mas antigua, si la fecha max es posterior a la min
              while (self.dateToday-pastTimeMax)<(self.dateToday-pastTimeMin):# max es anterior a min
                  print("La fecha máxima debe ser mayor a la fecha minima")
                  print("Tampoco pueden ser iguales")
                  #pide la fecha máxima
                  pastTimeTextMax=input("Ingrese hace cuanto tiempo fue el post (fecha máxima): ")
                  #pide la fecha minima
                  pastTimeTextMin=input("Ingrese hace cuanto tiempo fue el post (fecha minima): ")
                  #obtiene las fechas
                  pastTimeMax=getDate(pastTimeTextMax)
                  pastTimeMin=getDate(pastTimeTextMin)
              #Limpiar consola
              self.clearConsole()
              #Basicamente se tendra la lista de todos los posts que sean menor a la fecha maxima especificada.
              filterDate=False
              print("Inicia la búsqueda...")
              avoidMisleading=0#en caso que la persona haya dado like a un post antiguo, esto evitara que la busqueda pare
              #sera hasta 12 (4 posts si es que comento, likeo y compartio el mismo post)
              while (filterDate) and avoidMisleading<12:#normalmente dara false, 
                    #filtro por  tiempo
                    filterDate=self.getFilterDate(pastTimeMax)#funciona
                    if filterDate:#cambiar de true a false
                        avoidMisleading+=1
                        filterDate=False
                    else:#En caso que solo haya sido unos posts aislados antiguos, se reinicia el valor de la variable
                        avoidMisleading=0
                        
                    # Scroll down to bottom 
                    self.execute_script("window.scrollTo(0,document.body.scrollHeight);")
                    # Espera que cargue la pagina
                    time.sleep(scrollPauseTime)
              print("Termino la búsqueda...")
              def postsInTimeInterval(pastTimeMin):
                jsCodeAmountPosts="""
                        let finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];// no debo de colocar el let en lasegunda ejecucion a +, porque sale que es un redeclaracion
                        let postsToFilterDate= (finiteScroll.getElementsByClassName('feed-shared-update-v2 feed-shared-update-v2--minimal-padding full-height relative feed-shared-update-v2--e2e artdeco-card'));
                        return (postsToFilterDate.length);
                """
                #último post de la lista
                amountPosts = self.execute_script(f'{jsCodeAmountPosts}')
                
                firstPost=0
                #Se declara el tiempo de registro
                self.registerTime=datetime.now()
                #el primer post de la lista que sera mayor a pastTimeMin
                for i in range(amountPosts):
                    
                    jsCodeMin=f"""
                        let finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];
                        let postsToFilterDate= (finiteScroll.getElementsByClassName('feed-shared-update-v2 feed-shared-update-v2--minimal-padding full-height relative feed-shared-update-v2--e2e artdeco-card'));
                        let postToFilterDate= postsToFilterDate[{i}];//selecciona el post i
                        
                        let dateBox= postToFilterDate.getElementsByClassName('update-components-actor__sub-description t-12 t-normal t-black--light')[0];
                        let dateBoxSpan=dateBox.getElementsByTagName('span')[0];
                        let dateText=dateBoxSpan.textContent;//es la fecha con el formato "1 segundo/minuto/hora/dia/mes/año"
                        return (dateText);
                    """
                    firstPostInTimeInterval = self.execute_script(f'{jsCodeMin}')
                    firstPostDate=getDate(firstPostInTimeInterval)#transforma en fecha el texto
                    #la fecha del post es anterior a la fecha minima
                    
                    if firstPostDate>=pastTimeMin:#ve si la fecha del post es mayor al tiempo minimo
                        if i==0:
                            firstPost=0
                        else:
                            firstPost=i-1#el indice del post anterior al que cumple la condicion
                        break
                #No encontro un post dentro del intervalo
                
                jsCodePosts=f"""
                    let finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];
                    let postsToFilterDate= (finiteScroll.getElementsByClassName('feed-shared-update-v2 feed-shared-update-v2--minimal-padding full-height relative feed-shared-update-v2--e2e artdeco-card'));
                    let selectedPosts=Array.from(postsToFilterDate).slice({firstPost},postsToFilterDate.length)
                    return selectedPosts
            
                """
                 
                postsToShow= self.execute_script(f'{jsCodePosts}')
                
                return postsToShow
        
              print("Se consigue los posts dentro del intervalo")
              #Consigue los posts dentro del intervalo de tiempo
              postsToShow=postsInTimeInterval(pastTimeMin)
              #Si hay conexión a la nube, guarda a la persona buscada en user
              if  self.connectedWithCloud:
                 with self.pool.connect() as db_conn:
                    #Cambia el isDeleted de false a true
                    insert_stmt=f"""
                       CALL sp_insert_user('{searchedPersonName}','{profileLink}','{searchedPersonCountry}');

                    """
                    # eejecuta el stors procedure
                    #retorna el id de la persona buscada
                    searchedPersonId=db_conn.execute(insert_stmt)
                    db_conn.commit()#ESTO GUARDA LOS CAMBIOS.
              else:
                  #Para probar en local
                  searchedPersonId=1000
              #SE asigna el  tiempo de registro
              self.registerTimeInFormat =self.registerTime.strftime('%Y-%m-%d %H:%M:%S')

              try:
                for i in (postsToShow):
                    #crea objeto bs
                    postToShow=bs(i.get_attribute("innerHTML").encode("utf-8"),"html.parser")
                    #print(j)
                    try:
                        #promotion= postToShow.find("div",class_="update-components-text-view white-space-pre-wrap break-words").get_text()
                        subDescriptionPromotion=""
                        try: 
                            #descPromotion=self.execute_script(f'{jsCode}')
                            miniInfoBox=postToShow.find(
                            "div", class_="update-components-actor__meta relative")
                            descriptionPromotion=miniInfoBox.find(
                            "span", class_="update-components-actor__description t-12 t-normal t-black--light")
                            descriptionPromotionText= descriptionPromotion.find("span",class_="update-components-text-view white-space-pre-wrap break-words")
                            
                        except:
                            descriptionPromotionText=""
                        else:
                            try:
                                #Ve si hay una subdescripcion como Promocion
                                subDescriptionPromotion=miniInfoBox.find(
                                "div",class_="update-components-actor__sub-description t-12 t-normal t-black--light").get_text()
                            except:
                                subDescriptionPromotion=""
                            finally:
                                #Si el post no es promocion entra
                                if descriptionPromotionText!="Promocionado" and subDescriptionPromotion!="Promocionado":
                                    #Coge el texto
                                    try:
                                        textBox = postToShow.find("span",attrs={"class":"break-words"})
                                        text = textBox.find("span",attrs={"dir":"ltr"}).get_text()
                        
                                        try:
                                            #Consigue los de+ datos
                                            #fecha y hora registro
                                            finalPostDate=0
                                            dateBox=postToShow.find("div",class_="update-components-actor__meta relative")
                                            dateText=dateBox.find("span",
                                                class_="update-components-actor__sub-description t-12 t-normal t-black--light").find("span",
                                                {"aria-hidden":"true"}).get_text()
                                            listDateText=dateText.split(" ")
                                            if "segundo" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(seconds=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            elif "minuto" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(minutes=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            elif "hora" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(hours=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            elif "día" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(days=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            elif "semana" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(weeks=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            elif "mes" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(months=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            elif "año" in listDateText[1]:
                                                finalPostDate=(self.registerTime-relativedelta(years=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                            try:
                                                #print(finalPostDate)
                                                #print("Tiene fecha ",i)
                                                tagA = postToShow.find("a",           
                                                {"class":"app-aware-link update-components-actor__container-link relative display-flex flex-grow-1"})
                                                ownerPostProfileLink = tagA.get("href")
                                                   
                                            except Exception as noLink:
                                                print("noLink: ",noLink)
                                                self.errorsNoLink.append(postToShow)
                                            else:
                                                try:
                                                    ownerPostName= postToShow.find("span",attrs={"dir":"ltr"}).get_text()
                                                except Exception as noAuthor:
                                                    print("noAuthor: ",noAuthor)
                                                    self.errorsnoAuthor.append(postToShow)
                                                else:
                                                    try:
                                                        #print(ownerPostName)
                                                        infoComments=postToShow.find("ul",
                                                        {"class":"social-details-social-counts"})
                                                        amountCommentsText=infoComments.find("li",
                                                        class_="social-details-social-counts__item social-details-social-counts__comments social-details-social-counts__item--with-social-proof").get_text()
                                                        amountComments=int(amountCommentsText[:(amountCommentsText.find("c"))])
                                                    except:
                                                        amountComments=0
                                                    finally:
                                                        #self.execute_script(f'{jsCodeLinkPost}')
                                                        
                                                        #Filtrado de '
                                                        if "'" in ownerPostName:
                                                            ownerPostName=ownerPostName.replace("'","")
                                                        if "'" in text:
                                                            text=text.replace("'","")
                                                        ownerPostCountry=self.getUserCountry(ownerPostProfileLink)
                                                        #Comprueba si hay conexion a  internet para crear el statment 
                                                        if self.connectedWithCloud:

                                                            insert_stmt = f"""
                                                                
                                                                CALL sp_insert_specific_searche({searchedPersonId},'{ownerPostName}','{ownerPostProfileLink}',
                                                                                                '{ownerPostCountry}','{text}','{regTimeInFormat}',
                                                                                                '{finalPostDate}', {amountComments} );
                                                                """

                                                         
                                                        #Guarda los datos
                                                        self.insertQueriesSet.add((insert_stmt))#se agrega a la lista el query con los valores
                                                        #print(searchedPersonName)
                                                        #print(profileLink)
                                                        #print(ownerPostName)
                                                        #print(ownerPostProfileLink)
                                                        #print(text)
                                                        #print(regTimeInFormat)
                                                        #print(finalPostDate)
                                                        #print(amountComments)


                                        except Exception as noDate:
                                            print("noDate: ",noDate)
                                            self.errorsNoDate.append(postToShow)          
                                    except Exception as noPostText:
                                        print("noPostText :", noPostText)
                                        self.errorsNoPostText.append(postToShow)
                    except Exception as badPost:
                        print("badPost: ",badPost)
                        self.errorsBadPost.append(postToShow)
                    #finally:
                    #    j+=1
              except Exception as badPosts:
                    print("badPosts: ",badPosts)
                    self.errorsBadPosts.append(postsToShow)
              #finally:
              #      #cierra la ventana
              #      self.close()
          WebDriverWait(self,20).until(
            EC.presence_of_element_located((By.CLASS_NAME,'scaffold-finite-scroll__content')))
      except: 
          self.refresh #recarga la pagina si no se encuentra el elemento
          try:
              WebDriverWait(self,20).until(
                EC.presence_of_element_located((By.CLASS_NAME,'scaffold-finite-scroll__content')))
          except:
              print("No se pudo cargar la pagina")
              print("Verifique si el link es correcto")
              self.quit()
          else:
              makingTheSpecificSearching()
      else:
          makingTheSpecificSearching()
      

  def enterLinkedin(self):#porq se saltea el código?

    #entra a Linkedin
    self.get("https://pe.linkedin.com")
    #variable de refresh
    refresh=0
    #self.save_full_page_screenshot('/content/prueba1.png')
    while refresh<=2:
        try:
            print("refresh: ", refresh )
            #name=b4events.find_element(By.XPATH, "/html/body/main/section[1]/div/div/form/div[1]/input")
            #nombre de usuario
            #user="suarezmateo@gmail.com"
            userNameBox= WebDriverWait(self,30).until(
                                EC.presence_of_element_located((By.ID, "session_key"))
              )
            #self.find_element(By.ID, "session_key").send_keys(self.userName)
           
            #print('1')
        except:
            print('No esta el recuadro para el nombre. Recargar la pagina...')    
        
            self.refresh()
            refresh+=1
            """try:
            #name=b4events.find_element(By.XPATH, "/html/body/main/section[1]/div/div/form/div[1]/input")
            #nombre de usuario
            #user="suarezmateo@gmail.com"
            userNameBox= WebDriverWait(self,30).until(
                            EC.presence_of_element_located((By.ID, "session_key"))
          )
            userNameBox.send_keys(self.userName)

            print('1 1 ')
        except:
            print("No aparece el user box")
            print("Espere unos minutos para ejecutar...")
            print('1 1 1')
            self.quit()
        else:
            try:
                #contrase�a
                #password="Bomboperu123"
                userPasswordBox=self.find_element(By.ID, "session_password")
                print('1 2')
            except:
                print("No aparece el password box")
                print("Espere unos minutos para ejecutar...")
                self.quit()
                print('1 2 1')
            else:
                print('1 3')
                userPasswordBox.send_keys(self.userPassword)

                userPasswordBox.send_keys(Keys.ENTER)"""
            
        else:
            userNameBox.send_keys(self.userName)
            try:
                #contrase�a
                #password="Bomboperu123"
                userPasswordBox=self.find_element(By.ID, "session_password")
                #print('2')
            except:
                print("No aparece el password box")
                #print("Espere unos minutos para ejecutar...")
                self.refresh()
                refresh+=1
                
                #print('2 1')
            else:
                userPasswordBox.send_keys(self.userPassword)
                #print('3')

                userPasswordBox.send_keys(Keys.ENTER)
                break
  def changeToRecent(self):
     
      #variable refresh para recargar
      refresh=0
      while refresh<0:
          try:
              #Esperar a q aparezca el boton
              WebDriverWait(self,30).until(
                                    #EC.element_to_be_clickable((By.CLASS_NAME, "display-flex full-width artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom ember-view"))
                                    EC.element_to_be_clickeable((By.CLASS_NAME, "scaffold-layout__main"))
                                    )
          except:
              print("No ha cargado el botón para cambiar de Principal a Recientes")
              self.refresh()
          else:
              try:

                  #seleccione el boton y lo  clickee
                  jscode="""
                        let idMain = document.getElementById('main');
                        let line= idMain.getElementsByClassName('mb2 artdeco-dropdown artdeco-dropdown--placement-bottom artdeco-dropdown--justification-right ember-view')[0];
                        //window.alert(line.innerHTML);

                        //let buttonLine = line.getElementsByTagName('button')[0];
                        let buttonLine = line.getElementsByClassName('display-flex full-width artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom ember-view')[0];
                        buttonLine.click();
                        //window.alert(buttonLine.innerHTML);
                
                  """
          
                  self.execute_script(f'{jscode}')
              except:#Podría ser que se demoro  en cargar la pagina o un error de carga
                  #print("No clickeo el boton")
                  self.refresh()
              else:
                  #Encontro el boton
                  time.sleep(5)#Se tiene q esperar hasta que aparezca el html de las opciones
                  try:
                      jscodeClick="""
                                let idMain = document.getElementById('main');
                                let line= idMain.getElementsByClassName('mb2 artdeco-dropdown artdeco-dropdown--placement-bottom artdeco-dropdown--justification-right ember-view')[0];
                                 //sin tiempo de espera da error, no me deja utilziar timeout el linkedin
                                let options = line.getElementsByTagName('div')[1].getElementsByTagName('div')[2];
                                //(window.alert(options.innerHTML));
                                options.click();  
                      
                      """
                      self.execute_script(f'{jscodeClick}')
                  except:
                      #Es por siacaso se demorara más tiempo de lo normal
                      try:
                          self.execute_script(f'{jscodeClick}')
                      except:
                          print("No clickeo el boton para recientes...")
              #self.postLinkedin()
  def getFilterDate(self, dateToCompare):#Para el filtro por fecha
    try:
        #No funciona con selenium, por lo que haré con javascript
        #Da el elemento html de donde se sacará la fecha a evaluar
        #codigo en javascripts
        #Este puede dar promocionado o la fecha
        dateBoxFilterText=""
        jsCode="""
                let finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];
                let postsToFilterDate= (finiteScroll.getElementsByClassName('feed-shared-update-v2 feed-shared-update-v2--minimal-padding full-height relative feed-shared-update-v2--e2e artdeco-card'));
                let postToFilterDate= postsToFilterDate[postsToFilterDate.length-1];//selecciona el ultimo post
                let dateBox= postToFilterDate.getElementsByClassName('update-components-actor__sub-description t-12 t-normal t-black--light')[0];
                let dateBoxSpan=dateBox.getElementsByTagName('span')[0];
                
                let dateText=dateBoxSpan.textContent
                
                return (dateText);
        """
        #no colocar el window.alert() porque el codigo sigue en python y no regresa el dato a tiempo
        dateBoxFilterText = self.execute_script(f'{jsCode}')
        #Si el ultimo post, es una promocion...
        if dateBoxFilterText=="Promocionado":
            jsCodePromocionado="""
                let finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];
                let postsToFilterDate= (finiteScroll.getElementsByClassName('feed-shared-update-v2 feed-shared-update-v2--minimal-padding full-height relative feed-shared-update-v2--e2e artdeco-card'));
                let postToFilterDate= postsToFilterDate[postsToFilterDate.length-2];//selecciona el penultimo
                let dateBox= postToFilterDate.getElementsByClassName('update-components-actor__sub-description t-12 t-normal t-black--light')[0];
                let dateBoxSpan=dateBox.getElementsByTagName('span')[0];
                return dateBoxSpan.textContent;
        """
            #Que seleccione el penultimo
            dateBoxFilterText=self.execute_script(f'{jsCodePromocionado}')
       
        #var dateBoxInsideSpan=dateBoxSpan.getElementsByTagName('span');
    except:
        #intento conseguir la fecha, pero no se pudo
        return True
    else:      
        
        #Coge la fecha junto el indicador de tiempo
        listFilterDateText=dateBoxFilterText.split(" ")  
        print(listFilterDateText)
        #if i in listFilterDateText!="Promocionado":
        try:
            if "segundo" in listFilterDateText[1]:
                substractDate=(relativedelta(seconds=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
            elif "minuto" in listFilterDateText[1]:
                substractDate=(relativedelta(minutes=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
            elif "hora" in listFilterDateText[1]:
                substractDate=(relativedelta(hours=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
            elif "día" in listFilterDateText[1]:
                substractDate=(relativedelta(days=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
            elif "semana" in listFilterDateText[1]:
                substractDate=(relativedelta(weeks=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
            elif "mes" in listFilterDateText[1]:
                substractDate=(relativedelta(months=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
            elif "año" in listFilterDateText[1]:
                substractDate=(relativedelta(years=int(listFilterDateText[0])))
                #print(substractDate)
                filterPostDate=(self.dateToday-substractDate)
        except:
            #print("No tiene fecha: ",listFilterDateText[0])
            filterPostDate=self.dateToday
        finally:
            #Se compara la fecha del post con la fecha maxima a buscar
            #la fecha del post es anterior a la fecha de hoy-3meses
            #Para postLinkedin, la cosa es que siempre salga true y recien al final saldra un false, 
            #Para specificSearch, normalmente saldra false y la cosa es que al final de true, 
            #print("La fecha un post es: ",filterPostDate)
            #print('filterDate', filterPostDate)
            #print('datetocomapre', dateToCompare)
            return (filterPostDate>dateToCompare)#25>29 False, 25<24 True
  def getHTMLPosts(self):
    #variable refresh para recargar la pagina por errores
    refresh=0
    while refresh<1:

        try:
            elementRawPosts= WebDriverWait(self, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "scaffold-finite-scroll__content"))
    
            )      
        except:
            print("La pagina no ha cargado")
            self.refresh
            refresh+=1
        else:
            #Tiempo de pausa entre scroll para que carguen los posts
            scrollPauseTime= 2
    
            #en el feed se muestran al inicio 10 posts, pero no todos son visibles
            #m�s se baja en el feed, aparecen 5 post +, pero no todos son visibles
            filterDate=True
            numPost=0
            dateToCompare=self.antiqueMax
            while numPost<=5 and (filterDate) :#1000,
                #filtro por  tiempo
                print('filterdate ',filterDate)
                #print('numPost', numPost)
                filterDate=self.getFilterDate(dateToCompare)#funciona
                #filterDate=False
                # Scroll down to bottom 
                self.execute_script("window.scrollTo(0,document.body.scrollHeight);")

                # Espera que cargue la pagina
                time.sleep(scrollPauseTime)
                numPost+=1
            #print('filterdate ',filterDate)
            #print('numPost', numPost)
            #print('and:',numPost<=50 and (filterDate))
            #print("numPost<=10 and (filterDate):", str(numPost<=10 and (filterDate)))
            #print("numpost: ", str(numPost))
            #print("filterDate: ",str(filterDate))
            #Se asigna el tiempo actual en la variable registerTime
            self.registerTime=datetime.now()
            #Se asigna el tiempo con formato
            self.registerTimeInFormat=self.registerTime.strftime('%Y-%m-%d %H:%M:%S')
            #Se coge el elemento del scroll infinito
            #elementRawPosts=self.find_element(By.CLASS_NAME, "scaffold-finite-scroll__content")
            #Se cogen los posts
            rawPosts=elementRawPosts.get_attribute("innerHTML")
            #rawPosts = allPosts.find_elements(By.CLASS_NAME
                                       #,"feed-shared-update-v2__description-wrapper")  
            #Se coloca los post en formato
            allPostsToFilter=bs(rawPosts.encode("utf-8"),"html.parser")
            #se crea una lista con los posts en formato
            postsToFilter=allPostsToFilter.findAll("div",class_="artdeco-card")
            return (postsToFilter)
  def linkedinPostsOnFeed(self, postsToFilter):
    
    self.amountPosts=len(postsToFilter)
    print('cantidad post analizados: ',self.amountPosts)
    try:
        
        for postToFilter in (postsToFilter):#
            #print(j)
            mustBeSaved=False

            try:
                #Saca el texto
                #try:
                #    hashtagBox=postToFilter.find(
                #        "div", class_="feed-shared-contextual-header__meta").find(
                #            "a", {"class":"app-aware-link  update-components-text-view__hashtag"}
                #            )
                #except:
                #    hashtagBox=""
                #    #print("# vacio")
                #finally:
                #    if hashtagBox!="":
                #        isHashtag= True
                #si es anuncio de empleo...
                #si es hashtag...(feed-shared-contextual-header__meta
                #si es un poll...
                #no todos tienen esa clase, depende de si tienen seguidores o no
                
                #promotion= postToFilter.find("div",class_="update-components-text-view white-space-pre-wrap break-words").get_text()
                subDescriptionPromotion=""
                
                try: 
                    
                    #descPromotion=self.execute_script(f'{jsCode}')
                    miniInfoBox=postToFilter.find(
                    "div", class_="update-components-actor__meta relative")
                    descriptionPromotion=miniInfoBox.find(
                    "span", class_="update-components-actor__description t-12 t-normal t-black--light")
                    descriptionPromotionText= descriptionPromotion.find("span",class_="update-components-text-view white-space-pre-wrap break-words")
                    #print("descPromotion: ", descPromotion)
                    #print("descriptionP: ",descriptionPromotionText)
                except:
                    descriptionPromotionText=""
                else:
                    try:
                        subDescriptionPromotion=miniInfoBox.find(
                        "div",class_="update-components-actor__sub-description t-12 t-normal t-black--light").get_text()
                    except:
                        subDescriptionPromotion=""

                #Ve si publicidad o no
                if descriptionPromotionText!="Promocionado" and subDescriptionPromotion!="Promocionado":
                    
                    try:
                        #print("Paso promocionado: ",j)
                        textBox = postToFilter.find("span",
                                                    attrs={"class":"break-words"})
                    
                        text = textBox.find("span",attrs={"dir":"ltr"}).get_text()
                        #print(text)
                        
                        #if "evento" in text and "proveedor" in textelse:
                        #Si está conectado con la nube
                            
                                    
                        #Consigue las keywords presentes
                        foundKeywords=[]
                        #Itera en las keywordsText
                        for index,i in enumerate(self.keywordsText):
                            if mustBeSaved:
                                #Como se debe de guardar, se añaden los ids de las palabras que se encuentran en el post
                                if i in text:
                                        foundKeywords=foundKeywords.append(self.keywordsId[index])
                            elif i in text:
                                #Como una keyword esta en el post, se debe de guardar
                                mustBeSaved=True
                                foundKeywords.append(self.keywordsId[index])#Se guarda el id
                        if mustBeSaved:
                            #Consigue los datos restantes
                            try: 
                                #fecha y hora registro
                                finalPostDate=0
                                dateBox=postToFilter.find("div",class_="update-components-actor__meta relative")
                                dateText=dateBox.find("span",
                                    class_="update-components-actor__sub-description t-12 t-normal t-black--light").find("span",
                                    {"aria-hidden":"true"}).get_text()
                                #Transforma: 4 horas... a una lista de str
                                listDateText=dateText.split(" ")   
                                #transforma la lista str a una fecha
                                if "segundo" in listDateText[1]:
                                    finalPostDate=(self.registerTime-relativedelta(seconds=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                elif "minuto" in listDateText[1]:
                                    finalPostDate=(self.registerTime-relativedelta(minutes=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                elif "hora" in listDateText[1]:
                                    finalPostDate=(self.registerTime-relativedelta(hours=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                elif "día" in listDateText[1]:
                                    finalPostDate=(self.registerTime-relativedelta(days=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                elif "semana" in listDateText[1]:
                                    finalPostDate=(self.registerTime-relativedelta(weeks=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                elif "mes" in listDateText[1]:
                                    finalPostDate=(self.registerTime-relativedelta(months=int(listDateText[0]))).strftime('%Y-%m-%d %H:%M:%S')
                                #else:
                                #    finalPostDate=registerTime.strftime('%Y-%m-%d %H:%M:%S')
                                #    if finalPostDate==registerTime.strftime('%Y-%m-%d %H:%M:%S'):
                                #        print("Post sin fecha....")
                                #    self.errorsNoDate.append(postToFilter)
                                try:
                                    #print(finalPostDate)
                                    #print("Tiene fecha ",i)
                                    tagA = postToFilter.find("a",           
                                    {"class":"app-aware-link update-components-actor__container-link relative display-flex flex-grow-1"})
                                    profileLink = tagA.get("href")
                                                   
                                except Exception as noLink:
                                    print("noLink: ",noLink)
                                    self.errorsNoLink.append(postToFilter)
                                else:
                                    try:
                                        #print(tagA) 
                                        #print(j)
                                        ownerPostName= postToFilter.find("span",attrs={"dir":"ltr"}).get_text()
                                    except Exception as noAuthor:
                                        print("noAuthor: ",noAuthor)
                                        self.errorsnoAuthor.append(postToFilter)
                                    else:
                                        try:
                                            #print(ownerPostName)
                                            infoComments=postToFilter.find("ul",
                                            {"class":"social-details-social-counts"})
                                            amountCommentsText=infoComments.find("li",
                                            class_="social-details-social-counts__item social-details-social-counts__comments social-details-social-counts__item--with-social-proof").get_text()
                                            amountComments=int(amountCommentsText[:(amountCommentsText.find("c"))])
                                        except:
                                            amountComments=0
                                        finally:
                                                       
                                            
                                            #Filtrado de ' y "
                                            if "'" in ownerPostName:
                                                ownerPostName=ownerPostName.replace("'","")
                                            if "'" in text:
                                                text=text.replace("'","")

                                            personCountry=  self.getUserCountry(profileLink)
                                            #Query para guardar los datos
                                            call_stmt=f"""
                                                CALL insert_events ('{ownerPostName}', '{profileLink}','{personCountry}' ,
                                                '{text}' , '{regTimeInFormat}' , '{finalPostDate}', {amountComments}, '{self.keywordsIdToSave}', '{foundKeywords}');
                                                
                                            """
                                            insert_stmt = f"""INSERT INTO events (author_name,profile_link,post_text, register_time, post_time, amount_comments, keywords_used, keywords_present ) 
                                            VALUES ( );
                                            """
                                                       
                                            #Guarda los datos
                                            self.insertQueriesSet.add((call_stmt))#se agrega a la lista el query con los valores
                                                    
                                            #self.profileLinks.append(profileLink)#link
                                            #self.postsTexts.append(text)#texto post
                                            #self.postsDates.append(finalPostDate)
                                            #self.postComments.append(amountComments)#cantidad de comentarios
                                            #self.postsAuthors.append(ownerPostName)#nombre del autor
                                            #Lista de keywords presentes    
                                            #print("se guarda: ", str(j)) 
                                                
                            except Exception as noDate:
                                print("noDate: ",noDate)
                                self.errorsNoDate.append(postToFilter)   
                        
                    except Exception as noPostText:
                        print("noPostText :", noPostText)
                        self.errorsNoPostText.append(postToFilter)
            except Exception as badPost:
                print("badPost: ",badPost)
                self.errorsBadPost.append(postToFilter)
            #finally:
            #    j+=1
    except Exception as badPosts:
        
        print("badPosts: ",badPosts)
        self.errorsBadPosts.append(postsToFilter)
    #finally:
    #    self.close()#cierra la ventana, pero no la instancia


  def linkedinPostsFoundViaSearching(self):
    #variable de recarga
    refresh=0
    #Lista de html
    htmlPostList=[]
    while refresh<1:
        try:
            #Ve si la barra de busquedas cargo
            searchBar=WebDriverWait(self,30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-global-typeahead__input"))
                )
        except:
            #Si no cargo, recarga la pagina e intenta de nuevo ejecutar la busqueda
            print("No ha cargado la barra de búsqueda")
            self.refresh()
        else:
            #Tras encontrar la barra de busqueda, con cada keywords realiza una busqueda
            for i in self.keywordsText:
                #ingresa la keyword
                searchBar.send_keys(i)
                #presiona enter para  que se busque
                searchBar.send_keys(Keys.ENTER)
                try:
                    #Espera a que cargue los filtros de busqueda
                    searchFilter=WebDriverWait(self,30).until(
                        EC.presence_of_element_located((By.ID, "search-reusables__filters-bar"))
                        )
                except:
                    #si no cargaron recarga la pagina
                    print("No ha cargado los filtros de búsqueda")
                    self.refresh()
                else:
                    #Tras cargar las opciones de filtro,  presiona la primera opcion
                    searchFilterPostsOption=searchFilter.find_element(By.CLASS_NAME, "search-reusables__primary-filter").find_element(By.TAG_NAME, "button")
                    searchFilterPostsOption.click()
                    #Agrega los post en la lista
                    if boolean(htmlPostList):
                        #agrega a la lista existente los nuevos post
                        htmlPostList=htmlPostList+self.getHTMLPosts()
                    else:
                        #asigna a  la  lista vacia los posts
                        htmlPostList=self.getHTMLPosts()
                        searchBar.send_keys(Keys.DELETE)
            self.amountPosts=len(htmlPostList)
            print('cantidad post analizados: ',self.amountPosts)
            return htmlPostList
                    


  def saveErrors(self):
      with open("errores.html","w",encoding="utf-8") as file:
        file.write(("Cantidad de Post analizados: {}\n").format(self.amountPosts))
        file.write("errorsBadPosts:    \n")
        for i,j in enumerate(self.errorsBadPosts):
            file.write(("i: {}\n").format(i))
            file.write(("HTML: \n {}").format(j))
        file.write("errorsBadPost:    \n")
        for i,j in enumerate(self.errorsBadPost):
            file.write(("i: {}\n").format(i))
            file.write(("HTML: \n {}").format(j))
        file.write("errorsNoPostText:    \n")
        for i,j in enumerate(self.errorsNoPostText):
            file.write(("i: {}\n").format(i))
            file.write(("HTML: \n {}").format(j))
        file.write("errorsNoDate:    \n")
        for i,j in enumerate(self.errorsNoDate):
            file.write(("i: {}\n").format(i))
            file.write(("HTML: \n {}").format(j))
        file.write("errorsNoAuthor:    \n")
        for i,j in enumerate(self.errorsNoLink):
            file.write(("i: {}\n").format(i))
            file.write(("HTML: \n {}").format(j))
        file.write("errorsNoLink:    \n")
        for i,j in enumerate(self.errorsNoLink):
            file.write(("i: {}").format(i))
            file.write(("HTML: \n {}").format(j))
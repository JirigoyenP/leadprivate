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
              except:
                  print("Puede que cambiaran la clase del boton para Principal a Recientes")
              else:
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


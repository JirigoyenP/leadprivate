##link post
                                                        #jsCodeClickButton="""
                                                        #    var finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];
                                                        #    var twoOptions=  finiteScroll.getElementsByClassName('feed-shared-control-menu display-flex feed-shared-update-v2__control-menu absolute text-align-right feed-shared-update-v2--with-hide-post')[0];//numero del post
                                                        #    var buttonClick= twoOptions.getElementsByTagName('button')[0];
                                                        #    buttonClick.click()//abre el las opciones
                                                        #    //var optionCopyLink= twoOptions.getElementsByTagName('div')[1].getElementsByTagName('li')[1];//selecciona de la lista la opcion 2:la decopiar link
                                                        #    //window.alert(optionCopyLink.length)
                                                        #    //optionCopyLink.click();
                                                        #     """
                                                        #self.execute_script(f'{jsCodeClickButton}')
                                                        #time.sleep(5) #El tiempo que demora aparecer la lista
                                                        #jsCodeLinkPost="""
                                                        #    var finiteScroll = document.getElementsByClassName('scaffold-finite-scroll__content')[0];
                                                        #    var twoOptions=  finiteScroll.getElementsByClassName('feed-shared-control-menu display-flex feed-shared-update-v2__control-menu absolute text-align-right feed-shared-update-v2--with-hide-post')[0];//numero del post
                                                        #    //var buttonClick= twoOptions.getElementsByTagName('button')[0];
                                                        #    // buttonClick.click()//abre el las opciones
                                                        #    //Por siaca estoy repitiendo el click dl boton
                                                        #    var optionCopyLink= twoOptions.getElementsByTagName('div')[1].getElementsByTagName('li')[1];//selecciona de la lista la opcion 2:la decopiar link
                                                        #    //window.alert(optionCopyLink.length)
                                                        #    optionCopyLink.click();
                                                        #    async function copyPageUrl() {
                                                        #    try {
                                                        #        await navigator.clipboard.writeText(location.href);
                                                        #        window.alert("COPIO  URL  de la pagina");
                                                        #        console.log('Page URL copied to clipboard');
                                                        #    } catch (err) {
                                                        #        window.alert("Fallo escribir");
                                                        #        console.error('Failed to copy: ', err);
                                                        #        }
                                                        #    }
                                                        
                                                        #    async function getClipboardContents() {
                                                        #      try {
                                                        #        const text = await navigator.clipboard.readText();
                                                        #        window.alert("Lee lo copiado  de la pagina");
                                                        #        console.log('Pasted content: ', text);
                                                        #      } catch (err) {
                                                        #        window.alert("FALLO LEER");
                                                        #        console.error('Failed to read clipboard contents: ', err);
                                                        #      }
                                                        #    }
                                                        #    copyPageUrl();
                                                        #    getClipboardContents();
                                                      
                                                        #    """
                                                        #self.execute_script(f'{jsCodeLinkPost}')

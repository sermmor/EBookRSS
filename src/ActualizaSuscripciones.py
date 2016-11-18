#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse
import urllib2
import feedparser
import os


class RSSDownload(object):
    def __init__(self):
        self.sNameXmlFile = 'BlogsRSS.xml'
        self.listaRSS = []
        
    def sincronizaBlogs(self):
        def extraeLinksYPath():
            blogsDOM = parse(self.sNameXmlFile)
            # Extraemos path.
            blogPathDOM = blogsDOM.documentElement.getElementsByTagName('path')[0]
            sPath = blogPathDOM.childNodes[0].data
            # Extraemos lista links de suscripciones.
            blogsDOM = blogsDOM.documentElement.getElementsByTagName('blog')
            lSubcription = []
            for blogI in blogsDOM:
                lSubcription = lSubcription + [blogI.childNodes[0].data]
            return lSubcription, sPath
            
        def descargaImagen(sPathFile, url):
            '''
            Dada una url descarga la imagen a la carpeta sPathFile y devuelve la ruta.
            '''
            res = corregirTildes((url.split("/")[-1]))
            if not os.path.exists(sPathFile + "/images"):
                    # crear carpeta y bajar todos los post y guardarlos en la carpeta
                    os.mkdir(sPathFile + "/images")
            while os.path.exists(sPathFile + "/images/" + res):
                #Si ya existía en la caché un fichero con el mismo nombre, añadir un 1 delante.
                res = "1"+ res
            resPath = sPathFile + "/images/" + res
            f = urllib2.urlopen(url)
            fich = open(resPath, 'w')
            fich.write(f.read())
            fich.close()
            f.close()
            return "images/" + res
        
        def quitaEnlaces(sBody):
            # Quita todos los enlaces del tipo <a .... > </a>, para que no dé problemas.
            sBodyWithoutA = sBody.replace("</a>", "")
            lsNewBody = sBodyWithoutA.split("<a")
            sNewBody = ""
            for sElem in lsNewBody:
                initBloq = -1 # ">"
                bSinInit = False
                endBloq = -1 # "<"
                bSinEnd = False
                try:
                    initBloq = sElem.index("<")
                except:
                    bSinInit = True
                try:
                    endBloq = sElem.index(">")
                except:
                    bSinEnd = True
                    
                if bSinInit and bSinEnd:
                    sNewBody = sNewBody + sElem
                elif bSinInit:
                    # Hay que quitar la basura dejada tras el split de "<a"
                    sNewBody = sNewBody + sElem[sElem.index(">")+1:]
                elif bSinEnd:
                    sNewBody = sNewBody + sElem
                elif endBloq < initBloq:
                    # Hay que quitar la basura dejada tras el split de "<a"
                    sNewBody = sNewBody + sElem[sElem.index(">")+1:]
                else:
                    sNewBody = sNewBody + sElem
            return sNewBody
        
        def extractImages(sPathFile, sBody):
            def indexOr(caad, lSeparadores):
                encontrado = False
                j = 0
                res = -1
                jEnd = len(lSeparadores)
                while (j < jEnd) and (not encontrado):
                    try:
                        res = caad.index(lSeparadores[j])
                        encontrado = res > 0
                    except:
                        encontrado = False
                    j = j + 1
                if not encontrado:
                    res = jEnd - 1
                return res
            
            newBody = sBody
            # Calcular el path donde guardar las imágenes.
            sPathImages = ("/").join((sPathFile.split("/")[:-1]))
            # 1 - Extraer los links que se sepa que contienen imágenes.
            todosLosLinks = filter(lambda pal: pal[:3] == "://", sBody.split("http")) 
            todosLosLinks = map(lambda pal: "http" + pal[:indexOr(pal, ["\'", '\"'])], todosLosLinks)
            todosLosLinks = filter(lambda pal: pal[-4:].lower()==".jpg" or pal[-4:].lower()==".png" or pal[-4:].lower()==".gif" or pal[-4:].lower()==".bmp", todosLosLinks)
            # 2 - Descargar las imágenes en el sPathFile.
            listNewUrls = []
            for url in todosLosLinks:
                listNewUrls = listNewUrls + [descargaImagen(sPathImages, url)]
            # 3 - Cambiar los links de las imágenes en el newBody (con replace) por los "nuevos links" de las imágenes
            for i in range(len(todosLosLinks)):
                newBody = newBody.replace(todosLosLinks[i], listNewUrls[i])
            return quitaEnlaces(newBody)
        
        def savePost(sPathFile, body, sTitlePost, sDatePost, sAuthorPost):
            text = "<html>\n <head>\n <meta content='text/html; charset=UTF-8' http-equiv='Content-Type'/>\n </head>\n\n <body>\n" + "<h1>" + sTitlePost + "</h1>\n" + "<br><span style=\"font-size: x-small;\">" + sAuthorPost + ", " + sDatePost +"</span><br><br>" + extractImages(sPathFile, body) + "\n </body>\n</html>"
            fich = open(sPathFile, 'w')
            fich.write(text.encode('utf-8')) # Hacemos el encode para que no haya problemas al guardar.
            fich.close()
            
        def corregirTildes(sTextoHTML):
            sNewTexto = sTextoHTML.replace(u"á", "a").replace(u"é", "e").replace(u"í", "i").replace(u"ó", "o").replace(u"ú", "u").replace(u"ñ", "n").replace(u"Á", "A").replace(u"É", "E").replace(u"Í", "I").replace(u"Ó", "O").replace(u"Ú", "U").replace(u"Ñ", "N").replace(u"¿", "").replace(u"—", "").replace(u"¡", "").replace("\"", "").replace(".", "").replace(",", "").replace("\'", "").replace("?", "").replace("\n", "").replace(u"«", "").replace("@", "").replace("%", "").replace("_", "").replace("+", "").replace("/", "").replace("\\", "").replace(":", "").replace(";", "").replace(" ", "").replace("<", "").replace(">", "").replace("\t", "")
            return sNewTexto
        
        def estaFichero(sPathDir, blNameEntry):
            # Si en el directorio sPathDir (blNameEntry == corregirTildes(blEntry.Title) + ".html"), devuelve true, false en caso contrario.
            listaDirect = os.listdir(sPathDir)
            i = 0
            iEnd = len(listaDirect)
            encontrado = False
            while (i < iEnd) and (not encontrado):
                aproxNameFile = listaDirect[i]
                try:
                    aproxNameFile = aproxNameFile[(aproxNameFile.index(" - ") + len(" - ")):]
                    encontrado = (blNameEntry == aproxNameFile)
                except:
                    encontrado = False
                i = i + 1
            return encontrado
        
        def getLastIndex(sPathDir):
            lastIndex = "1000000"
            listaDirect = os.listdir(sPathDir)
            listaDirect.sort()
            if (len(listaDirect) != 0):
                lastIndex = str(int(listaDirect[0][:listaDirect[0].index(" - ")]) - 1)
            # Comparar con el número de cifras de "1000000" para añadir ceros, hasta que tenga una longitud de 7 cifras.
            if (len("1000000") != len(lastIndex)):  
                lastIndex = "0"*(len("1000000") - len(lastIndex)) + lastIndex
            return lastIndex
        
        def extractListUpdates(lBlogEntries, sPathDir):
            # Devuelvo una lista con sólo entradas a actualizar.Es decir de la blog.entries salvaje, filtra los que ya están en el sPathDir.
            lBlogEntriesToUpdate = []
            for blEntry in lBlogEntries:
                sNameFile = corregirTildes(blEntry.title) + '.html'
                # Compruebo si el fichero existe, si no existe añadir a lBlogEntriesToUpdate
                if not estaFichero(sPathDir, sNameFile): #not os.path.exists(sPathDir + "/" + sNameFile):
                    lBlogEntriesToUpdate = lBlogEntriesToUpdate + [blEntry]
            return lBlogEntriesToUpdate
            
        
        def sincronizeMain():
            #1º Sacar los links de suscripciones y la carpeta en las que guardarlas del fichero xml.
            lLinks, sPathDirSaveBlogs = extraeLinksYPath()
            iiEnd = len(lLinks)
            ii = 0 # Si iiEnd es el 100%, ii es el (ii*100/iiEnd)%
            for linkRSS in lLinks:
                #2º Saco la suscripción al link.
                theBlog = feedparser.parse(linkRSS)
                #3º Comprobar por el título de cada blog, si éste existe como carpeta en sPathDirSaveBlogs, paso al paso 4, si no existe crear carpeta y bajar todos los post y guardarlos en la carpeta.
                sNameDir = sPathDirSaveBlogs + "/" + corregirTildes(theBlog.feed.title)
                llBlogEntries = []
                if not os.path.exists(sNameDir):
                    # crear carpeta y bajar todos los post y guardarlos en la carpeta
                    os.mkdir(sNameDir)
                    llBlogEntries = theBlog.entries
                else:
                    #4º Comparar la lista de post (Cada post tendrá como nombre de fichero: blog.entries[0].published + blog.entries[0].title + '.html') con la lista de los ficheros de la carpeta, para sacar la lista de los que debemos de bajar.
                    llBlogEntries = extractListUpdates(theBlog.entries, sNameDir)
                # Guardamos la lista de entradas.
                llBlogEntries.reverse() # se hace reverse para que todo quede en el orden adecuado.
                sLastIndexBlog = getLastIndex(sNameDir)
                for theEntry in llBlogEntries:
                    sPathFileEntry = sNameDir + "/" + sLastIndexBlog + " - " + corregirTildes(theEntry.title) + ".html"
                    try:
                        savePost(sPathFileEntry, theEntry.content[0]['value'], theEntry.title, theEntry.published, theEntry.author)
                    except:
                        try:
                            savePost(sPathFileEntry, theEntry.summary_detail['value'], theEntry.title, theEntry.updated, theEntry.author)
                        except:
                            print "Error al guardar: " + sPathFileEntry
                    # Calcular el próximo indice.
                    sLastIndexBlog = str(int(sLastIndexBlog) - 1)
                    if (len("1000000") != len(sLastIndexBlog)):  
                        sLastIndexBlog = "0"*(len("1000000") - len(sLastIndexBlog)) + sLastIndexBlog
                ii = ii + 1
                print "-> " + str(ii*100/iiEnd) + "% completado."
                # Abrir la carpeta de suscripciones.
                #os.system("dolphin \"" + sPathDirSaveBlogs + "\"")
        
        sincronizeMain()
           
    def addSuscripcion(self, sPathRSS):
        None
       
       

rss = RSSDownload()
rss.sincronizaBlogs()


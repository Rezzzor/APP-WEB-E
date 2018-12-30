# regularite-TER.py
# Correpond au corrigé du dernier exercice du TD3+4 (TD3-s7.py)

import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as pltd

import sqlite3

def multiplication_liste(L):
    """ Fonction qui réalise un changement d'échelle des données."""
    res=[0 for k in L]
    for k in range(len(L)):
        res[k]=L[k]*1/10
    return (res)

#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  #
  # On surcharge la méthode qui traite les requêtes GET
  #
  
  def do_GET(self):

    # On récupère les étapes du chemin d'accès
    self.init_params()
    
    """print("*-*-*")
    print("En 0:" + str(self.path_info[0]))
    print(self.path_info)
    print("*-*-*")"""
    # le chemin d'accès commence par /time
    if self.path_info[0] == 'time':
      self.send_time()
   
     # le chemin d'accès commence par /regions
    elif self.path_info[0] == 'regions':
      self.send_regions()
      
    # le chemin d'accès commence par /ponctualite
    elif self.path_info[0] == 'ponctualite':
      self.send_ponctualite()
      
    elif self.path_info[0] == 'YearSpan':
        self.send_ponctualite(True)
        
    # ou pas...
    else:
      self.send_static()
      
    # On regarde ensuite dans la Query
    
    

  #
  # On surcharge la méthode qui traite les requêtes HEAD
  #
  def do_HEAD(self):
    self.send_static()

  #
  # On envoie le document statique demandé
  #
  def send_static(self):

    # on modifie le chemin d'accès en insérant un répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)
  
  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    #print("PATH INFO",self.path_info)
    #self.query_string = info.query
    # On split la query pour la mettre dans un tableau
    #self.query_tab = [elem.split('=') for elem in info.query.split('&')]
    #print("*-*QUERY TAB*-* ",self.query_tab)
    # [ ['year1','2010'], ['year2','2012'] ]
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' :
        self.params = parse_qs(self.body)
    else:
      self.body = ''
   
    # traces
    #print('info_path =',self.path_info)
    #print('body =',length,ctype,self.body)
    #print('params =', self.params)
    
  #
  # On envoie un document avec l'heure
  #
  def send_time(self):
    
    # on récupère l'heure
    time = self.date_time_string()

    # on génère un document au format html
    body = '<!doctype html>' + \
           '<meta charset="utf-8">' + \
           '<title>l\'heure</title>' + \
           '<div>Voici l\'heure du serveur :</div>' + \
           '<pre>{}</pre>'.format(time)

    # pour prévenir qu'il s'agit d'une ressource au format html
    headers = [('Content-Type','text/html;charset=utf-8')]

    # on envoie
    self.send(body,headers)

  #
  # On génère et on renvoie la liste des régions et leur coordonnées (version TD3)
  #
  def send_regions(self):

    conn = sqlite3.connect('temp.sqlite')
    c = conn.cursor()
    
    c.execute("SELECT * FROM 'stations_meteo'")
    r = c.fetchall()
    
    headers = [('Content-Type','application/json')];
    body = json.dumps([{'s':staid, 'nom':n, 'lat':lat, 'lon': lon} for (staid,n,lat,lon) in r])
    self.send(body,headers)

  #
  # On génère et on renvoie un graphique pour la température sur tous les relevés
  #
  def send_ponctualite(self, query = False):

    conn = sqlite3.connect('temp.sqlite')
    c = conn.cursor()
    
    if query == False:
        if len(self.path_info) <= 1 or self.path_info[1] == '' :   # pas de paramètre => liste par défaut
            # Definition des régions et des couleurs de tracé
            STAID = [31,32,33] #Ne sert à rien
        else:
            # On teste que la station demandée existe bien
            c.execute("SELECT DISTINCT STAID FROM 'TG_1978-2018'")
            reg = c.fetchall()
            if (self.path_info[1],) in reg:   # Rq: reg est une liste de tuples
              STAID = [(self.path_info[1],"blue")]
            else:
                print ('Erreur nom')
                self.send_error(404)    # Région non trouvée -> erreur 404
                return None
    else:
        STAID = [(self.params['STAID'][0],"blue")]
    
    # configuration du tracé, ne change pas avec la query
    fig1 = plt.figure(figsize=(18,6))
    ax = fig1.add_subplot(111)
    ax.set_ylim(bottom=-5,top=35)
    ax.grid(which='major', color='#888888', linestyle='-')
    ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
    ax.xaxis.set_major_locator(pltd.YearLocator())
    ax.xaxis.set_minor_locator(pltd.MonthLocator())
    ax.xaxis.set_major_formatter(pltd.DateFormatter('%Y'))
    ax.xaxis.set_tick_params(labelsize=5)
    ax.xaxis.set_label_text("Date")
    ax.yaxis.set_label_text("Temperature (en degré)")


    # boucle sur les régions
    if query == False:
        for l in (STAID) :
            c.execute("SELECT * FROM 'TG_1978-2018' WHERE STAID=?",l[:1])  # ou (l[0],)
            r = c.fetchall()
            # recupération de la date (colonne 2) et transformation dans le format de pyplot
            x = [pltd.date2num(dt.date(int(a[2][0:4]),int(a[2][4:6]),int(a[2][6:]))) for a in r]
            # récupération de la régularité (colonne 8)
            y = [float(a[3]) for a in r]
    else:
        #print("self.params['STAID'] ",self.params['STAID'])
        c.execute("SELECT * FROM 'TG_1978-2018' WHERE STAID=?",self.params['STAID'])  # ou (l[0],)
        r = c.fetchall()
        R = []
        debut = int(self.params['debut'][0])
        fin = int(self.params['fin'][0])
        
        for elem in r:
            year = int(elem[2][0:4])
            #print(year,debut,fin)
            if year >= debut and year <= fin:
                R.append(elem)
        
        x = [pltd.date2num(dt.date(int(a[2][0:4]),int(a[2][4:6]),int(a[2][6:]))) for a in R]
        # récupération de la régularité (colonne 8)
        y = [float(a[3]) for a in R]
    
    
    y_fin = multiplication_liste(y)
    # tracé de la courbe
    plt.plot(x,y_fin,linewidth=0.2, linestyle='-', marker='o', color="blue", label=str(STAID[0][0]))
            
    # légendes
    plt.legend(loc='lower left')
    plt.title('Températures au cours du temps',fontsize=16) 

    # génération des courbes dans un fichier PNG
    fichier = 'courbes/ponctualite_'+str(STAID[0][0]) +'.png'
    plt.savefig('client/{}'.format(fichier))
    plt.close()
    
    html='<!DOCTYPE html><title>Temperature</title>' +\
    '<meta charset="utf-8">' +\
    '<img src="/{}?{}" alt="ponctualite {}" width="100%">'.format(fichier,self.date_time_string(),self.path)
    body = json.dumps({
            'title': 'Température pour la station n° '+str(STAID[0][0]), \
            'img': '/'+fichier \
             });
    print("BODY",body)
    # on envoie
    # headers = [('Content-Type','application/json')];
    self.send(html)
    
  #
  # On envoie les entêtes et le corps fourni
  #
  def send(self,body,headers=[]):

    # on encode la chaine de caractères à envoyer
    encoded = bytes(body, 'UTF-8')

    # on envoie la ligne de statut
    self.send_response(200)

    # on envoie les lignes d'entête et la ligne vide
    [self.send_header(*t) for t in headers]
    self.send_header('Content-Length',int(len(encoded)))
    self.end_headers()

    # on envoie le corps de la réponse
    self.wfile.write(encoded)

 
#
# Instanciation et lancement du serveur
#
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()


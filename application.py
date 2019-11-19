from flask import Flask, render_template, request, redirect, url_for, flash, request, redirect, url_for, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
import os, requests, time, feedparser, re, datetime
from database_setup import Base, Representative, Senator, HouseBills, SenateBills
# from terms import *
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from random import *

application = Flask(__name__)

engine = create_engine('sqlite:///legislators.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = scoped_session(sessionmaker(bind=engine))

@application.teardown_request
def remove_session(ex=None):
    session.remove()
##------------------------------------------------##
## Static variables
all_counties_in_pa = ['philadelphia', 'allegheny', 'montgomery', 'bucks', 'delaware', 'lancaster', 'chester', 'york', 'berks', 'westmoreland',
'lehigh', 'luzerne', 'northampton', 'erie', 'dauphin', 'cumberland', 'lackawanna', 'washington', 'butler', 'beaver',
'monroe', 'schuylkill', 'fayette', 'cambria', 'centre', 'franklin', 'lebanon', 'blair', 'mercer', 'lycoming',
'adams', 'northumberland', 'lawrence', 'crawford', 'indiana', 'clearfield', 'somerset', 'armstrong', 'columbia', 'bradford',
'carbon', 'pike', 'venango', 'wayne', 'bedford', 'huntingdon', 'mifflin', 'jefferson', 'perry', 'union',
'mckean', 'susquehanna', 'warren', 'tioga', 'clarion', 'greene', 'snyder', 'clinton', 'elk', 'wyoming', 'juniata',
'potter', 'montour', 'fulton', 'sullivan', 'forest', 'cameron']
##------------------------------------------------##
## show_published
show_published = True
##------------------------------------------------##
## url_for cache buster
@application.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(application.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
##------------------------------------------------##
## Error Handlers
@application.errorhandler(404)
def error404(e):
    return render_template('couldnotfind.html', error_type='404'), 404

@application.errorhandler(500)
def error500(e):
    return render_template('couldnotfind.html', error_type='500'), 500
##------------------------------------------------##
## Rep Finder
def RepFinder(street_address, city, zipcode):
    try:
        geolocator = Nominatim()
        place = geolocator.geocode(street_address + ' ' + city + ' ' + zipcode)

        try:
            lat = str(place.latitude)
            lon = str(place.longitude)

            url  = 'http://www.legis.state.pa.us/cfdocs/legis/home/findyourlegislator/?doSearch=yes&addr='
            url += street_address.replace(' ','+')
            url += '&city='
            url += city.replace(' ','+')
            url += '&zipCode='
            url += zipcode
            url += '&fullAddr='
            url += street_address.replace(' ','+')
            url += '%2C+'
            url += city.replace(' ','+')
            url += '%2C+PA%2C+'
            url += zipcode
            url += '&geoLat='
            url += lat
            url += '&geoLng='
            url += lon
            url += '&geoResponse=OK#address'

            # City Hall
            # req = 'http://www.legis.state.pa.us/cfdocs/legis/home/findyourlegislator/?doSearch=yes&addr=1401+John+F+Kennedy+Blvd&city=Philadelphia&zipCode=19107&fullAddr=1401+John+F+Kennedy+Blvd%2C+Philadelphia%2C+PA%2C+19107&geoLat=39.9541298&geoLng=-75.16439909999997&geoResponse=OK%2C+PARTIAL+MATCH#address'

            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table', {'class': 'ResultTable'})

            # Spin through the table rows
            # for r, row in enumerate(table.findAll('tr')):
            #     cells = row.findAll('td')
            #     for c, cell in enumerate(cells):
            #         print r, c, '--->', cell.text.strip()

            rep =        list(list(table.findAll('tr'))[0])[3].text.strip()
            house_dist = int(list(list(table.findAll('tr'))[0])[5].text.strip().split()[-1])

            sen =        list(list(table.findAll('tr'))[1])[3].text.strip()
            sen_dist =   int(list(list(table.findAll('tr'))[1])[5].text.strip().split()[-1])

            return {'rep_first_name'    : rep.split()[0].title(),
                    'rep_last_name'     : rep.split()[1].title(),
                    'house_dist'        : int(house_dist),
                    'sen_first_name'    : sen.split()[0].title(),
                    'sen_last_name'     : sen.split()[1].title(),
                    'sen_dist'          : int(sen_dist)}

        except AttributeError:
            return False

    except: #will catch any error
        return False


## Google Maps URL for office addresses
def officeGoogleMaps(address):
    address = address.replace(' ','+').replace('\n','+').replace(',','+')
    loop_again = True #eliminates multiple '+' in a row
    while loop_again == True:
        loop_again = False
        for i in range(len(address)):
            try:
                if address[i] == '+' and address[i+1] == '+':
                    address = address[:i] + address[i+1:]
                    loop_again = True
                    break
            except IndexError:
                pass
    if address[-1] == '+': #eliminates trailing '+'
        address = address[:-1]
    return 'https://www.google.com/maps/search/?api=1&query=' + address

##------------------------------------------------##

@application.route('/')
def splash():
    if randint(1,2) == 1:
        bills = [session.query(HouseBills).filter_by().first()]
        bill_from = 'house'
    else:
        bills = [session.query(SenateBills).filter_by().first()]
        bill_from = 'senate'

    if randint(1,2) == 1:
        legislators = [list(session.query(Representative).filter_by().all())[randint(1,202)]]
        chamber = 'house'
    else:
        legislators = [list(session.query(Senator).filter_by().all())[randint(1,49)]]
        chamber = 'senate'
    return render_template('splash.html', bills=bills, legislators=legislators, chamber=chamber, bill_from=bill_from, name = 'capitol.jpg')

@application.route('/about/')
def about():
    return render_template('about.html')

# @application.route('/find-legislators/', methods=['GET','POST'])
# def findRep():
#     if request.method == 'POST':
#         foundreps = RepFinder(request.form['streetaddress'],request.form['city'],request.form['zipcode'])
#         if foundreps == False:
#             rep = None
#             sen = None
#         else:
#             rep = session.query(Representative).filter_by(dist=foundreps['house_dist']).one()
#             sen = session.query(Senator).filter_by(dist=foundreps['sen_dist']).one()
#         return render_template('yourrep.html', rep=rep, sen=sen, foundreps=foundreps)
#     else:
#         return render_template('getrep.html')

@application.route('/house/<int:dist>/')
def repProfile(dist):
    ##----------------------- REP ATTRIBUTES -----------------------#
    ## rep.dist         (int)
    ## rep.last_name    (str)
    ## rep.first_name   (str)
    ## rep.sex          (str)
    ## rep.party        (str)
    ## rep.gov_bio      (str)
    ## rep.counties     (str) --> counties                  (list)
    ## rep.rep_since    (str) --> rep_since                 (list)
    ## rep.committees   (str) --> committees_leadership     (list)
    ## rep.dist_phone   (str) --> dist_phone                (list)
    ## rep.dist_fax     (str) --> dist_fax                  (list)
    ## rep.cap_phone    (str)
    ## rep.cap_fax      (str)
    ## rep.dist_address (str) --> dist_address              (list)
    ## rep.cap_address  (str)
    ## rep.pers_site    (str)
    ## rep.facebook     (str)
    ## rep.twitter      (str)
    ## rep.youtube      (str)
    ## rep.leadership   (str) --> committees_leadership     (list)

    rep = session.query(Representative).filter_by(dist=dist).one() ##Defines an instance of a Representative

    ##--- COMMITTEES_LEADERSHIP ---##
    committees = []
    leadership = []
    committees_leadership = []
    if rep.committees != None: ## rep.committees == None only if rep.leadership != None
        committees=rep.committees.split('%') ## So it either displays committees or leadership
    if rep.leadership != None:
        leadership=rep.leadership.split('%')
    for i in leadership:
        committees_leadership.append(i)
    for i in committees:
        committees_leadership.append(i)

    ##--- COUNTIES ---##
    counties=rep.counties.split('%') ## There is no instance other than a VACANT seat where rep.conties == None

    ##--- REP_SINCE ---##
    rep_since = rep.rep_since.split(',')

    ##--- DIST_PHONE ---##
    if rep.dist_phone != None:
        dist_phone = rep.dist_phone.split('%')
        for phone in dist_phone:
            if phone == '~': ## Sets elements of dist_phone equal to None when no number exists
                dist_phone[dist_phone.index(phone)] = None
    else:
        dist_phone = [None]

    ##--- DIST_FAX ---##
    if rep.dist_fax != None:
        dist_fax = rep.dist_fax.split('%')
        for fax in dist_fax:
            if fax == '~': ## Sets elements of dist_phone equal to None when no number exists
                dist_fax[dist_fax.index(fax)] = None
    else:
        dist_fax = [None]

    ##--- DIST_ADDRESS ---##
    if rep.dist_address != None:
        dist_address = rep.dist_address.split('%')
    else:
        dist_address = [None]

    ##--- COMMITTEES_RAW ---#
    committees_raw = [committee.split(',')[0] for committee in committees_leadership]

    sponsored_bills = session.query(HouseBills).filter_by(primesponsor=rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist)).all()

    cosponsored_bills = session.query(HouseBills).filter(HouseBills.cosponsors.contains(rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist))).all()

    return render_template('rep_profile.html', rep=rep, elected_position='representative', counties=counties,
                            rep_since=rep_since, committees_leadership=committees_leadership, dist_phone=dist_phone,
                            dist_fax=dist_fax, dist_address=dist_address, chamber='house',
                            committees_raw=committees_raw, sponsored_bills=sponsored_bills, cosponsored_bills=cosponsored_bills,
                            show_published=show_published, officeGoogleMaps=officeGoogleMaps)

@application.route('/senate/<int:dist>/')
def senProfile(dist):
    sen = session.query(Senator).filter_by(dist=dist).one() ##Defines an instance of a Senator

    ##--- COMMITTEES_LEADERSHIP ---##
    committees = []
    leadership = []
    committees_leadership = []
    if sen.committees != None: ## sen.committees == None only if sen.leadership != None
        committees=sen.committees.split('%') ## So it either displays committees or leadership
    if sen.leadership != None:
        leadership=sen.leadership.split('%')
    for i in leadership:
        committees_leadership.append(i)
    for i in committees:
        committees_leadership.append(i)

    ##--- COUNTIES ---#
    counties=sen.counties.split('%') ## There is no instance other than a VACANT seat where sen.conties == None

    ##--- SEN_SINCE ---##
    sen_since = sen.sen_since.split(',')

    ##--- DIST_PHONE ---##
    if sen.dist_phone != None:
        dist_phone = sen.dist_phone.split('%')
        for phone in dist_phone:
            if phone == '~': ## Sets elements of dist_phone equal to None when no number exists
                dist_phone[dist_phone.index(phone)] = None
    else:
        dist_phone = [None]

    ##--- DIST_FAX ---##
    if sen.dist_fax != None:
        dist_fax = sen.dist_fax.split('%')
        for fax in dist_fax:
            if fax == '~': ## Sets elements of dist_phone equal to None when no number exists
                dist_fax[dist_fax.index(fax)] = None
    else:
        dist_fax = [None]

    ##--- DIST_ADDRESS ---##
    if sen.dist_address != None:
        dist_address = sen.dist_address.split('%')
    else:
        dist_address = [None]

    ##--- COMMITTEES_RAW ---#
    committees_raw = [committee.split(',')[0] for committee in committees_leadership]


    sponsored_bills = session.query(SenateBills).filter_by(primesponsor=sen.first_name + ' ' + sen.last_name + '*' + str(sen.dist)).all()
    cosponsored_bills = session.query(SenateBills).filter(SenateBills.cosponsors.contains(sen.first_name + ' ' + sen.last_name + '*' + str(sen.dist))).all()

    return render_template('rep_profile.html', elected_position='senator', rep=sen, counties=counties,
                            rep_since=sen_since, committees_leadership=committees_leadership,
                            dist_phone=dist_phone, dist_fax=dist_fax, dist_address=dist_address, chamber='senate',
                            committees_raw=committees_raw, sponsored_bills=sponsored_bills, cosponsored_bills=cosponsored_bills,
                            show_published=show_published, officeGoogleMaps=officeGoogleMaps)

@application.route('/house/', methods=['GET','POST'])
def HouseDirectory():
    search = None
    if request.method == 'POST':
        reps = []
        is_search = True
        search = request.form['search_reps'].strip().lower()
        if search == '':
            reps = session.query(Representative).filter_by().all()
            is_search = False

        elif search.isdigit():
            reps = session.query(Representative).filter_by(dist=search).all()

        elif search.split()[0] in all_counties_in_pa:
            reps = session.query(Representative).filter(Representative.counties.contains(search)).all()
        else:
            try:
                reps = session.query(Representative).filter(Representative.last_name.contains(search.strip().split()[1])).all()
            except IndexError:
                reps = session.query(Representative).filter(Representative.last_name.contains(search.strip())).all()
            reps2 = session.query(Representative).filter(Representative.first_name.contains(search.split()[0])).all()

            if len(search.split()) > 1:
                reps = [i for i in reps2 if i in reps]
            else:
                reps += [i for i in reps2 if i not in reps]

    else:
        reps = session.query(Representative).filter_by().all()
        is_search = False

    return render_template('directory.html', reps=reps, chamber='rep', is_search=is_search, search=search)


@application.route('/senate/', methods=['GET','POST'])
def SenateDirectory():
    search = None
    if request.method == 'POST':
        reps = []
        is_search = True
        search = request.form['search_reps'].strip().lower()
        if search == '':
            reps = session.query(Senator).filter_by().all()
            is_search = False

        elif search.isdigit():
            reps = session.query(Senator).filter_by(dist=search).all()

        elif search.split()[0] in all_counties_in_pa:
            reps = session.query(Senator).filter(Senator.counties.contains(search)).all()

        else:
            try:
                reps = session.query(Senator).filter(Senator.last_name.contains(search.strip().split()[1])).all()
            except IndexError:
                reps = session.query(Senator).filter(Senator.last_name.contains(search.strip())).all()
            reps2 = session.query(Senator).filter(Senator.first_name.contains(search.split()[0])).all()

            if len(search.split()) > 1:
                reps = [i for i in reps2 if i in reps]
            else:
                reps += [i for i in reps2 if i not in reps]

    else:
        reps = session.query(Senator).filter_by().all()
        is_search = False

    return render_template('directory.html', reps=reps, chamber='sen', is_search=is_search, search=search)


# committees_dashes = {'COMMUNICATIONS & TECHNOLOGY': 'COMMUNICATIONS-&-TECHNOLOGY', 'TRANSPORTATION': 'TRANSPORTATION', 'TOURISM & RECREATIONAL DEVELOPMENT': 'TOURISM-&-RECREATIONAL-DEVELOPMENT', 'RULES & EXECUTIVE NOMINATIONS': 'RULES-&-EXECUTIVE-NOMINATIONS', 'ENVIRONMENTAL RESOURCES & ENERGY': 'ENVIRONMENTAL-RESOURCES-&-ENERGY', 'LOCAL GOVERNMENT': 'LOCAL-GOVERNMENT', 'AGING & OLDER ADULT SERVICES': 'AGING-&-OLDER-ADULT-SERVICES', 'COMMERCE': 'COMMERCE', 'NONE': 'NONE', 'LIQUOR CONTROL': 'LIQUOR-CONTROL', 'LABOR & INDUSTRY': 'LABOR-&-INDUSTRY', 'APPROPRIATIONS': 'APPROPRIATIONS', 'CONSUMER AFFAIRS': 'CONSUMER-AFFAIRS', 'URBAN AFFAIRS & HOUSING': 'URBAN-AFFAIRS-&-HOUSING', 'AGING & YOUTH': 'AGING-&-YOUTH', 'LAW & JUSTICE': 'LAW-&-JUSTICE', 'INTERGOVERNMENTAL OPERATIONS': 'INTERGOVERNMENTAL-OPERATIONS', 'CHILDREN & YOUTH': 'CHILDREN-&-YOUTH', 'BANKING & INSURANCE': 'BANKING-&-INSURANCE', 'GAME & FISHERIES': 'GAME-&-FISHERIES', 'GAMING OVERSIGHT': 'GAMING-OVERSIGHT', 'COMMITTEE ON COMMITTEES': 'COMMITTEE-ON-COMMITTEES', 'CONSUMER PROTECTION & PROFESSIONAL LICENSURE': 'CONSUMER-PROTECTION-&-PROFESSIONAL-LICENSURE', 'APPROPRIATIONS, EX-OFFICIO': 'APPROPRIATIONS,-EX-OFFICIO', 'PROFESSIONAL LICENSURE': 'PROFESSIONAL-LICENSURE', 'AGRICULTURE & RURAL AFFAIRS': 'AGRICULTURE-&-RURAL-AFFAIRS', 'FINANCE': 'FINANCE', 'DEVELOPMENT': 'DEVELOPMENT', 'URBAN AFFAIRS': 'URBAN-AFFAIRS', 'STATE GOVERNMENT': 'STATE-GOVERNMENT', 'JUDICIARY': 'JUDICIARY', 'INSURANCE': 'INSURANCE', 'COMMUNITY, ECONOMIC & RECREATIONAL DEVELOPMENT': 'COMMUNITY,-ECONOMIC-&-RECREATIONAL-DEVELOPMENT', 'HUMAN SERVICES': 'HUMAN-SERVICES', 'HEALTH': 'HEALTH', 'VETERANS AFFAIRS & EMERGENCY PREPAREDNESS': 'VETERANS-AFFAIRS-&-EMERGENCY-PREPAREDNESS', 'EDUCATION': 'EDUCATION', 'TOURISM & RECREATIONAL': 'TOURISM-&-RECREATIONAL', 'HEALTH & HUMAN SERVICES': 'HEALTH-&-HUMAN-SERVICES'}
#
# house_committees = ['AGING & OLDER ADULT SERVICES', 'GAMING OVERSIGHT', 'JUDICIARY', 'APPROPRIATIONS', 'PROFESSIONAL LICENSURE', 'TOURISM & RECREATIONAL', 'LABOR & INDUSTRY', 'LIQUOR CONTROL', 'URBAN AFFAIRS', 'GAME & FISHERIES', 'CHILDREN & YOUTH', 'ENVIRONMENTAL RESOURCES & ENERGY', 'PROFESSIONAL LICENSURE', 'EDUCATION', 'LIQUOR CONTROL', 'COMMITTEE ON COMMITTEES', 'LABOR & INDUSTRY', 'VETERANS AFFAIRS & EMERGENCY PREPAREDNESS', 'COMMERCE', 'ENVIRONMENTAL RESOURCES & ENERGY', 'JUDICIARY', 'CONSUMER AFFAIRS', 'HEALTH', 'TRANSPORTATION', 'FINANCE', 'GAMING OVERSIGHT', 'JUDICIARY', 'APPROPRIATIONS', 'AGRICULTURE & RURAL AFFAIRS', 'TOURISM & RECREATIONAL DEVELOPMENT', 'INSURANCE', 'LOCAL GOVERNMENT', 'INSURANCE', 'URBAN AFFAIRS', 'TOURISM & RECREATIONAL DEVELOPMENT', 'VETERANS AFFAIRS & EMERGENCY PREPAREDNESS', 'STATE GOVERNMENT', 'STATE GOVERNMENT', 'COMMITTEE ON COMMITTEES', 'TRANSPORTATION', 'HUMAN SERVICES', 'DEVELOPMENT', 'LOCAL GOVERNMENT']
#
# senate_committees = ['COMMUNICATIONS & TECHNOLOGY', 'JUDICIARY', 'URBAN AFFAIRS & HOUSING', 'LABOR & INDUSTRY', 'HEALTH & HUMAN SERVICES', 'LABOR & INDUSTRY', 'RULES & EXECUTIVE NOMINATIONS', 'APPROPRIATIONS, EX-OFFICIO', 'GAME & FISHERIES', 'ENVIRONMENTAL RESOURCES & ENERGY', 'EDUCATION', 'HEALTH & HUMAN SERVICES', 'BANKING & INSURANCE', 'VETERANS AFFAIRS & EMERGENCY PREPAREDNESS', 'NONE', 'RULES & EXECUTIVE NOMINATIONS', 'URBAN AFFAIRS & HOUSING', 'TRANSPORTATION', 'AGING & YOUTH', 'FINANCE', 'APPROPRIATIONS', 'AGRICULTURE & RURAL AFFAIRS', 'VETERANS AFFAIRS & EMERGENCY PREPAREDNESS', 'INTERGOVERNMENTAL OPERATIONS', 'COMMUNITY, ECONOMIC & RECREATIONAL DEVELOPMENT', 'LAW & JUSTICE', 'STATE GOVERNMENT', 'TRANSPORTATION', 'CONSUMER PROTECTION & PROFESSIONAL LICENSURE', 'LOCAL GOVERNMENT']
#
# @application.route('/house/<committee>')
# def houseCommittee(committee):
#     reps = session.query(Representative).filter(Representative.committees.contains(committee.replace('-',' '))).all()
#
#     if committee.upper() not in house_committees + senate_committees:
#         return abort(404)
#     else:
#         return render_template('committee_directory.html', reps=reps, chamber='rep', committee=committee)


# @application.route('/wiki/<page>')
# def Wiki(page):
#     return render_template('wiki.html', terms=wiki_terms[page.lower()], page=page.lower())

@application.route('/legislation/house/', methods=['GET','POST'])
def houseBills():
    search = None
    error = None
    category = None
    is_search = False
    pass_search = None
    if request.method == 'POST':
        is_search = True
        category = request.form['search-by']
        bills = []
        search = request.form['search_legislation'].strip().lower()
        pass_search = request.form['search_legislation'].strip()
        if search == '' and category not in ['passed-house','passed-senate','enacted']:
            bills = session.query(HouseBills).filter_by().all()
            is_search = False

        elif category == 'id':
            bills = session.query(HouseBills).filter_by(search_id=search.upper()).all()

        elif category == 'primesponsor':
            try:
                reps = session.query(Representative).filter(Representative.last_name.contains(search.strip().split()[1])).all()
            except IndexError:
                reps = session.query(Representative).filter(Representative.last_name.contains(search.strip())).all()
            reps2 = session.query(Representative).filter(Representative.first_name.contains(search.split()[0])).all()

            if len(search.split()) > 1:
                reps = [i for i in reps2 if i in reps]
            else:
                reps += [i for i in reps2 if i not in reps]

            s = [session.query(HouseBills).filter(HouseBills.primesponsor.contains(rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist))).all() for rep in reps]
            for i in s:
                for j in i:
                    if j not in bills:
                        bills.append(j)

        elif category == 'cosponsor':
            try:
                reps = session.query(Representative).filter(Representative.last_name.contains(search.strip().split()[1])).all()
            except IndexError:
                reps = session.query(Representative).filter(Representative.last_name.contains(search.strip())).all()
            reps2 = session.query(Representative).filter(Representative.first_name.contains(search.split()[0])).all()

            if len(search.split()) > 1:
                reps = [i for i in reps2 if i in reps]
            else:
                reps += [i for i in reps2 if i not in reps]

            s = [session.query(HouseBills).filter(HouseBills.cosponsors.contains(rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist))).all() for rep in reps]
            for i in s:
                for j in i:
                    if j not in bills:
                        bills.append(j)

        elif category == 'date':
            if len(search.split('/')) == 3:
                date = '-'.join(['0'+i if len(i) == 1 else i for i in [search.split('/')[2], search.split('/')[0], search.split('/')[1]]])
            elif len(search.split('-')) == 3:
                date = '-'.join(['0'+i if len(i) == 1 else i for i in [search.split('-')[2], search.split('-')[0], search.split('-')[1]]])
            else:
                error = 'formating'
            if error == None:
                bills = session.query(HouseBills).filter_by(published=date).all()

        elif category == 'keyword':
            bills = session.query(HouseBills).filter(HouseBills.summary.contains(search)).all()
            bills2 = session.query(HouseBills).filter(HouseBills.summary.contains(search.upper())).all()
            bills = list(set(list(bills)) | set(list(bills2)))

        elif category == 'committee':
            bills = session.query(HouseBills).filter_by(committees=search.upper()).all()

        elif category == 'passed-house':
            bills = session.query(HouseBills).filter_by(passedhouse='YES').all()

        elif category == 'passed-senate':
            bills = session.query(HouseBills).filter_by(passedsenate='YES').all()

        elif category == 'enacted':
            bills = session.query(HouseBills).filter_by(enacted='YES').all()

    else:
        bills = session.query(HouseBills).filter_by().all()

    return render_template('bills.html', bills=bills, chamber='house', error=error,
                            category=category, search=pass_search,
                            is_search=is_search, show_published=show_published)

@application.route('/legislation/senate/', methods=['GET','POST'])
def senateBills():
    search = None
    error = None
    category = None
    is_search = False
    pass_search = None
    if request.method == 'POST':
        is_search = True
        category = request.form['search-by']
        bills = []
        search = request.form['search_legislation'].strip().lower()
        pass_search = request.form['search_legislation'].strip()
        if search == '' and category not in ['passed-house','passed-senate','enacted']:
            bills = session.query(SenateBills).filter_by().all()
            is_search = False

        elif category == 'id':
            bills = session.query(SenateBills).filter_by(search_id=search.upper()).all()

        elif category == 'primesponsor':
            try:
                reps = session.query(Senator).filter(Senator.last_name.contains(search.strip().split()[1])).all()
            except IndexError:
                reps = session.query(Senator).filter(Senator.last_name.contains(search.strip())).all()
            reps2 = session.query(Senator).filter(Senator.first_name.contains(search.split()[0])).all()

            if len(search.split()) > 1:
                reps = [i for i in reps2 if i in reps]
            else:
                reps += [i for i in reps2 if i not in reps]

            s = [session.query(SenateBills).filter(SenateBills.primesponsor.contains(rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist))).all() for rep in reps]
            for i in s:
                for j in i:
                    if j not in bills:
                        bills.append(j)

        elif category == 'cosponsor':
            try:
                reps = session.query(Senator).filter(Senator.last_name.contains(search.strip().split()[1])).all()
            except IndexError:
                reps = session.query(Senator).filter(Senator.last_name.contains(search.strip())).all()
            reps2 = session.query(Senator).filter(Senator.first_name.contains(search.split()[0])).all()

            if len(search.split()) > 1:
                reps = [i for i in reps2 if i in reps]
            else:
                reps += [i for i in reps2 if i not in reps]

            s = [session.query(SenateBills).filter(SenateBills.cosponsors.contains(rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist))).all() for rep in reps]
            for i in s:
                for j in i:
                    if j not in bills:
                        bills.append(j)

        elif category == 'date':
            if len(search.split('/')) == 3:
                date = '-'.join(['0'+i if len(i) == 1 else i for i in [search.split('/')[2], search.split('/')[0], search.split('/')[1]]])
            elif len(search.split('-')) == 3:
                date = '-'.join(['0'+i if len(i) == 1 else i for i in [search.split('-')[2], search.split('-')[0], search.split('-')[1]]])
            else:
                error = 'formating'
            if error == None:
                bills = session.query(SenateBills).filter_by(published=date).all()

        elif category == 'keyword':
            bills = session.query(SenateBills).filter(SenateBills.summary.contains(search)).all()
            bills2 = session.query(SenateBills).filter(SenateBills.summary.contains(search.upper())).all()
            bills = list(set(list(bills)) | set(list(bills2)))

        elif category == 'committee':
            bills = session.query(SenateBills).filter_by(committees=search.upper()).all()

        elif category == 'passed-house':
            bills = session.query(SenateBills).filter_by(passedhouse='YES').all()

        elif category == 'passed-senate':
            bills = session.query(SenateBills).filter_by(passedsenate='YES').all()

        elif category == 'enacted':
            bills = session.query(SenateBills).filter_by(enacted='YES').all()

    else:
        bills = session.query(SenateBills).filter_by().all()

    return render_template('bills.html', bills=bills, chamber='senate', error=error,
                            category=category, search=pass_search,
                            is_search=is_search, show_published=show_published)

if __name__ == '__main__':
    application.debug = False
    application.run()

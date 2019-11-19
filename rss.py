#!/usr/bin/python

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from database_setup import Base, HouseBills, Representative, SenateBills, Senator
import feedparser, time, datetime
from progress.bar import Bar

print '\nUpdating legislation...'
print 'Scraping online records...'

## testing doing this first, instead of in each function. That way internet can be disconected
houseBillsFeed = feedparser.parse('http://www.legis.state.pa.us/WU01/LI/RSS/HouseBills.xml')
senateBillsFeed = feedparser.parse('http://www.legis.state.pa.us/WU01/LI/RSS/SenateBills.xml')
print 'Records gathered'

engine = create_engine('sqlite:///legislators.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

all_committees = ['AGING & OLDER ADULT SERVICES', 'LIQUOR CONTROL', 'CONSUMER AFFAIRS', 'HEALTH',
'TRANSPORTATION', 'FINANCE', 'RULES', 'GAMING OVERSIGHT', 'JUDICIARY',
'VETERANS AFFAIRS & EMERGENCY PREPAREDNESS', 'PROFESSIONAL LICENSURE', 'COMMERCE',
'LABOR & INDUSTRY', 'APPROPRIATIONS', 'STATE GOVERNMENT', 'COMMITTEE ON COMMITTEES',
'COMMITTEE ON ETHICS', 'HUMAN SERVICES', 'AGRICULTURE & RURAL AFFAIRS',
'TOURISM & RECREATIONAL DEVELOPMENT', 'URBAN AFFAIRS', 'GAME & FISHERIES',
'CHILDREN & YOUTH', 'ENVIRONMENTAL RESOURCES & ENERGY', 'EDUCATION', 'INSURANCE', 'LOCAL GOVERNMENT']

months = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}

def houseNameCase(name):
    if name == 'SCHLEGEL CULVER': return 'Schlegel Culver*108'
    new_name = ''
    wasLower = False
    for index, letter in enumerate(name.strip()):
        if index == 0:
            new_name += letter.upper()
        else:
            if wasLower == True:
                new_name += letter.upper()
                wasLower = False
            else:
                new_name += letter.lower()
            if letter.islower() or letter in ['-',"'",' ']:
                wasLower = True

    if new_name == 'Schlegel Culver': return 'Schlegel Culver*108'

    if len(name.split()) < 2:
        try:
            rep = session.query(Representative).filter_by(last_name=new_name).one()
            return rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist)
        except NoResultFound:
            return None
    else:
        first_initial = new_name.split()[0][0]
        last_name = new_name.split()[-1]
        last_name_reps = [rep.dist for rep in session.query(Representative).filter_by(last_name=last_name).all()]
        first_initial_reps = [rep.dist for rep in session.query(Representative).filter_by().all() if rep.first_name[0] == first_initial]
        reps = [i for i in first_initial_reps if i in last_name_reps]
        try:
            rep = session.query(Representative).filter_by(dist=reps[0]).one()
            return rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist)
        except IndexError:
            return None

def senateNameCase(name):
    new_name = ''
    wasLower = False
    for index, letter in enumerate(name.strip()):
        if index == 0:
            new_name += letter.upper()
        else:
            if wasLower == True:
                new_name += letter.upper()
                wasLower = False
            else:
                new_name += letter.lower()
            if letter.islower() or letter in ['-',"'",' ']:
                wasLower = True

    if len(name.split()) < 2:
        try:
            rep = session.query(Senator).filter_by(last_name=new_name).one()
            return rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist)
        except NoResultFound:
            return None
    else:
        first_initial = new_name.split()[0][0]
        last_name = new_name.split()[-1]
        last_name_reps = [rep.dist for rep in session.query(Senator).filter_by(last_name=last_name).all()]
        first_initial_reps = [rep.dist for rep in session.query(Senator).filter_by().all() if rep.first_name[0] == first_initial]
        reps = [i for i in first_initial_reps if i in last_name_reps]
        try:
            rep = session.query(Senator).filter_by(dist=reps[0]).one()
            return rep.first_name + ' ' + rep.last_name + '*' + str(rep.dist)
        except IndexError:
            return None


def updateHouseBills():
    day = datetime.datetime.today().day
    start = time.clock()
    # print 'Gathering house RSS feed...'
    # bills = feedparser.parse('http://www.legis.state.pa.us/WU01/LI/RSS/HouseBills.xml')
    bills = houseBillsFeed
    if bills.entries[0].id == session.query(HouseBills).filter_by().all()[0].bill_id and day % 5 != 0:
        print 'House legislation up to date'
    else:
        session.query(HouseBills).delete()

        bar = Bar('Updating house legislation', max=len(bills.entries))

        for bill in bills.entries:

        #-----ID-----#
            ID = bill.id

        #-----TITLE-----#
            title =  ' '.join(bill.title.split()[:3])

        #-----SEARCHID-----#
            if 'Bill' in bill.title:
                search_id = 'HB' + title.split()[-1]
            else:
                search_id = 'HR' + title.split()[-1]

        #-----SUMMARY-----#
            summary = bill.summary

        #-----PRIMESPONSOR-----#
            primesponsor = houseNameCase(' '.join(bill.parss_primesponsor.split()[1:]))

        #-----COSPONSOR-----#
            if bill.parss_cosponsors != '':
                if 'and' in bill.parss_cosponsors:
                    cosponsors_names = bill.parss_cosponsors.split(',')
                    cosponsors_names += cosponsors_names[-1].split(' and ')
                    cosponsors_names.pop(-3)
                    cosponsors_names = [cosponsor.strip() for cosponsor in cosponsors_names]
                    cosponsors_dists = [str(houseNameCase(i)) for i in cosponsors_names]

                    cosponsors = '%'.join(cosponsors_dists)
                else:
                    cosponsors = houseNameCase(bill.parss_cosponsors)
            else:
                cosponsors = None

        #-----PASSEDHOUSE-----#
            passedhouse = bill.parss_passedhouse

        #-----PASSEDSENATE-----#
            passedsenate = bill.parss_passedsenate

        #-----ENACTED-----#
            enacted = bill.parss_enacted

        #-----LASTACTION-----#
            if bill.parss_lastaction != '':
                lastaction = bill.parss_lastaction
            else:
                lastaction = None

        #-----LINK-----#
            link = bill.link

        #-----PUBLISHED-----#
            published = bill.published.split()[1:4][2] + '-' + months[bill.published.split()[1:4][1]] + '-' + bill.published.split()[1:4][0]
            # published = '-'.join(bill.published.split()[1:4])

        #-----COMMITTEES-----#
            try:
                committees = [i for i in all_committees if i in bill.parss_lastaction][0]
            except IndexError:
                committees = None

            x = HouseBills(search_id=search_id, bill_id=ID,title=title, summary=summary,
                            primesponsor=primesponsor, cosponsors=cosponsors,
                            passedhouse=passedhouse, passedsenate=passedsenate, enacted=enacted,
                            lastaction=lastaction, link=link, published=published, committees=committees)
            session.add(x)
            bar.next()

        session.commit()
        bar.finish()
        print 'House legislation updated in %f seconds' % (time.clock()-start)

def updateSenateBills():
    day = datetime.datetime.today().day
    start = time.clock()
    # print 'Gathering senate RSS feed...'
    # bills = feedparser.parse('http://www.legis.state.pa.us/WU01/LI/RSS/SenateBills.xml')
    bills = senateBillsFeed
    if bills.entries[0].id == session.query(SenateBills).filter_by().all()[0].bill_id and day % 5 != 0:
        print 'Senate legislation up to date'
    else:
        session.query(SenateBills).delete()

        bar = Bar('Updating senate legislation', max=len(bills.entries))

        for bill in bills.entries:

        #-----ID-----#
            ID = bill.id

        #-----TITLE-----#
            title =  ' '.join(bill.title.split()[:3])

        #-----SEARCHID-----#
            if 'Bill' in bill.title:
                search_id = 'SB' + title.split()[-1]
            else:
                search_id = 'SR' + title.split()[-1]

        #-----SUMMARY-----#
            summary = bill.summary

        #-----PRIMESPONSOR-----#
            if bill.parss_primesponsor != '':
                primesponsor = senateNameCase(' '.join(bill.parss_primesponsor.split()[1:]))
            else:
                primesponsor = None

        #-----COSPONSOR-----#
            if bill.parss_cosponsors != '':
                if 'and' in bill.parss_cosponsors:
                    cosponsors_names = bill.parss_cosponsors.split(',')
                    cosponsors_names += cosponsors_names[-1].split(' and ')
                    cosponsors_names.pop(-3)
                    cosponsors_names = [cosponsor.strip() for cosponsor in cosponsors_names]
                    cosponsors_dists = [str(senateNameCase(i)) for i in cosponsors_names]

                    cosponsors = '%'.join(cosponsors_dists)
                else:
                    cosponsors = senateNameCase(bill.parss_cosponsors)
            else:
                cosponsors = None

        #-----PASSEDHOUSE-----#
            passedhouse = bill.parss_passedhouse

        #-----PASSEDSENATE-----#
            passedsenate = bill.parss_passedsenate

        #-----ENACTED-----#
            enacted = bill.parss_enacted

        #-----LASTACTION-----#
            if bill.parss_lastaction != '':
                lastaction = bill.parss_lastaction
            else:
                lastaction = None

        #-----LINK-----#
            link = bill.link

        #-----PUBLISHED-----#
            published = bill.published.split()[1:4][2] + '-' + months[bill.published.split()[1:4][1]] + '-' + bill.published.split()[1:4][0]

        #-----COMMITTEES-----#
            try:
                committees = [i for i in all_committees if i in bill.parss_lastaction][0]
            except IndexError:
                committees = None

            x = SenateBills(search_id=search_id, bill_id=ID,title=title, summary=summary,
                            primesponsor=primesponsor, cosponsors=cosponsors,
                            passedhouse=passedhouse, passedsenate=passedsenate, enacted=enacted,
                            lastaction=lastaction, link=link, published=published, committees=committees)
            session.add(x)
            bar.next()

        session.commit()
        bar.finish()
        print 'Senate legislation updated in %f seconds' % (time.clock()-start)

# def deleteBills():
#     session.query(SenateBills).delete()
#     session.query(HouseBills).delete()
#     session.commit()

if __name__ == '__main__':
    updateHouseBills()
    updateSenateBills()
    print

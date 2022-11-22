luigi.configuration.get_config().set('core', 'default_scheduler_host', 'luigid-s')

def startZeppelinNotebook(id):
    #todo: get id by name,
    #potential: make server and port configurable, pass parameters to notebook
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5,  status_forcelist=(500, 429))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    headers = {"accept": "application/json","Content-Type": "application/json"}
    #first reset paragraph output
    reseturl="http://zeppelin-server:80/api/notebook/"+id +"/clear"
    reset_response = session.put(reseturl, headers=headers)
    #now start it
    url="http://zeppelin-server:80/api/notebook/job/" + id
    response = session.post(url, headers=headers)
    #search_response = requests.get(search_url, headers = search_headers)
    #print("url:", url)
    if response.status_code == 200:
        response_json = response.json()
        #print(response_json)
        res=response_json['status']
    else: 
        print("Error. Response Status:", response.status_code)
        print("url:", url)
    return res

def getZeppelinNotebookStatus(id, time):
    #pseudo: check all paragraphs, concatenate all paragraph results, calculate overall status (running, error, success)

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5,  status_forcelist=(500, 429))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    url="http://zeppelin-server:80/api/notebook/job/" + str(id)
    headers = {"accept": "application/json","Content-Type": "application/json"}
    response = session.get(url, headers=headers)
    #search_response = requests.get(search_url, headers = search_headers)
    #print("url:", url)
    status="ERROR"
    if response.status_code == 200:
        response_json = response.json()
        #print(response_json)
        dfStatus=pd.DataFrame.from_dict(response_json['body']['paragraphs'])
        dfStatus.dropna(subset=['status', 'finished'], inplace=True)
        startTimes=dfStatus['started'].apply(lambda x: strptime(x,'%a %b %d %H:%M:%S %Z %Y'))
        lastStartTime=startTimes.agg(max)
        if lastStartTime<time.timetuple(): #last starttime in notebook is less the the start of the job, thus, not started
            status="NOT STARTED"
        elif (dfStatus['status'].agg(max)==dfStatus['status'].agg(min) and dfStatus['status'].agg(min)=="FINISHED"):
            status="FINISHED"
        else:
            status="NOT FINSHED"   
    else: 
        print("Response Status:", response.status_code)
        print("url:", url)
        status="ERROR"

    #print("Status: " + status + " lastStartTime: " +strftime('%d %m %Y %H:%M:%S',lastStartTime) + " time: " +strftime('%d %m %Y %H:%M:%S',time.timetuple()))
    return status, dfStatus
    
class ZeppelinNotebookTarget(luigi.Target):
    """
    This target checks if the notebook executed successfully.
    """

    def __init__(self, id, time):
        self.host = "zeppelin-server"
        self.port = "80"
        self.id = id
        self.time=time

    def exists(self):
        print("in exists")
        status, dfStatus=getZeppelinNotebookStatus(self.id,self.time)
        return (status=="FINISHED")

#z.runNote('2HHJ45XF5') #Dazu braucht es einen gemeinsamen kontext (interpreter binding: globaly shared)

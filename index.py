from flask import Flask, jsonify, render_template, request,session
import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import numpy
from numpy import array
import shutil
from OMPython import OMCSession
import tempfile
import re
app = Flask(__name__)
app.secret_key = 'c\x9e\xdf\xf4\xfc\x15\x84A\xc3\xda\x8d\xdf\xbd\x10\x07\x88C\x10L\xff\xc6h&\n'

sessionobj={}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evalexpression', methods=['POST'])
def evalexpression():
    #print 'inside eval'
    try:
        text_content=request.form['input']
        div_content =request.form['output']
        sidcheck=request.form['sid'] 
        #print sidcheck 
        getomcobj=sessionobj[sidcheck]
        #sys.stdout.flush()    
        eval(text_content,div_content,getomcobj)    
        data="\n".join(session['msg'])
        del session['msg'][:]     
        return data 
    except:
        return "failed"    
	
@app.route('/createsession', methods=['POST'])
def createsession():
        ## Create a new omc session for the users and allot a seperate working directory for the session ##
        #print 'creating omc session'
        session['msg']=[]
        session['mat']=[]
        sid=request.form['sid']
        session['tmpdir'] = tempfile.mkdtemp()
        #print session['tmpdir'] 
        os.chdir(session['tmpdir'])
        sess=OMCSession()
        sessionobj[sid]=sess
        #print sessionobj
        #sys.stdout.flush()
        return "success"

@app.route('/deletesession', methods=['POST'])
def deletesession():
       ## delete the omc object and process when the user leaves the browser ##
       #print "Deleting"
       os.chdir("..")
       sid1=request.form['sid']
       if (len(sessionobj)!=0):
           omcobj=sessionobj[sid1]
           #print omcobj.sendExpression("getClassNames()")
           omcobj.__del__()
           #print 'objdeleted'
           try:
               shutil.rmtree(session['tmpdir'],True)
           except Exception as e:
               print e
       #sys.stdout.flush()
       return "deleted"

    
def eval(var1,var2,omc):
   ##run the evaluations in temp directory  ##
   #print 'evalexpression'
   
   x1=var1.split('#')
   y1=var2.split(',')
   x=filter(None,x1)
   y=filter(None,y1)
  
   for i in xrange(len(x)):
      z="\n".join(x[i].splitlines())
      z1 = filter(lambda x: not re.match(r'^\s*$', x), z)
      #z1="".join(x[i].splitlines())
      simcommand=z1.replace(' ','').startswith('simulate(')and z1.replace(' ','').endswith(')')
      plotcommand=z1.replace(' ','').startswith('plot(')and z1.replace(' ','').endswith(')')
     
      if (simcommand==True):
        try:
          s=omc.sendExpression(z1)
          name=s['resultFile']
          addmsg=s['messages']
          if (name!=''):
             session['mat'].append(name)          
             tempres="".join(['Simulation Success: Temp/',os.path.basename(name)])
             divcontent=" ".join(['<div id='+y[i]+'>','<b>',str(tempres),'</b>','</div>'])
          else:
             error=omc.sendExpression("getErrorString()")
             finalmsg=error+addmsg
             divcontent=" ".join(['<div id='+y[i]+' align="justify" >','<b>',str(finalmsg),'</b>','</div>'])
        except:
           divcontent=" ".join(['<div id='+y[i]+'>','<b>','failed()','</b>','</div>'])         
        
        session['msg'].append(divcontent)
      
      elif (plotcommand==True):   
          l1=z1.replace(' ','')
          l=l1[0:-1]
          plotvar=l[5:].replace('{','').replace('}','')
          divcontent=" ".join(['<div id='+y[i]+'>'])
          session['msg'].append(divcontent)
          plotdivid=y[i]
          plotgraph(plotvar,plotdivid,omc)
      else:
          try:
            l=omc.sendExpression(z)
          except:
            #l="failed()"
            l=omc.sendExpression(z,parsed=False)
            
          divcontent=" ".join(['<div id='+y[i]+'>','<b>',str(l).replace('<','&lt;').replace('>','&gt;'),'</b>','</div>'])
          session['msg'].append(divcontent)
   
   ## delete the process ##
   ##omc.__del__()
   #os.chdir("..")   
   
def plotgraph(plotvar,divid,omc):
  
  ## Function to handle plotting in browser ##
  
  if (len(session['mat'])!=0):
     res=session['mat'][-1]
     try:
       readResult = omc.sendExpression("readSimulationResult(\"" + os.path.basename(res) + "\",{time," + plotvar + "})")
       omc.sendExpression("closeSimulationResultFile()")
       plotlabels=['Time']
       exp='(\s?,\s?)(?=[^\[]*\])|(\s?,\s?)(?=[^\(]*\))'
       #print 'inside_plot1'
       subexp=re.sub(exp,'$#',plotvar)
       plotvalsplit=subexp.split(',')
       #print plotvalsplit
       for z in xrange(len(plotvalsplit)):
           val= plotvalsplit[z].replace('$#',',')
           plotlabels.append(val)
       #print plotlabels  
       plotlabel1=[x.encode('UTF8') for x in plotlabels]
       
       plots=[]
       for i in xrange(len(readResult)):   
         x=readResult[i]
         d=[]
         for z in xrange(len(x)):
            tu=x[z]
            d.append((tu,))
         plots.append(d)            
       n=numpy.array(plots)
       numpy.set_printoptions(threshold='nan')
       dygraph_array= repr(numpy.hstack(n)).replace('array',' ').replace('(' ,' ').replace(')' ,' ')
       dygraphoptions=" ".join(['{', 'legend:"always",','labels:',str(plotlabel1),'}'])
       data="".join(['<script type="text/javascript"> g = new Dygraph(document.getElementById('+'"'+str(divid)+'"'+'),',str(dygraph_array),',',dygraphoptions,')','</script>']) 
       divcontent="\n".join([str(data),"</div>"])
       session['msg'].append(divcontent)
     except:
       error=omc.sendExpression("getErrorString()")
       divcontent="".join(['<b>',error,'</b>',"</div>"])
       session['msg'].append(divcontent)
      
  else:
     divcontent="".join(['<b>','No result File Generated','</b>',"</div>"])
     session['msg'].append(divcontent)
    
    

if __name__ == '__main__':
    #app.run(debug=True,use_reloader=True)
    app.run(host='0.0.0.0')

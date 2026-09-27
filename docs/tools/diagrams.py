import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Circle, Rectangle
from matplotlib import font_manager
import numpy as np

INK="#17332E"; BRAND="#2E6B5E"; MINT="#EAF3F0"; LINE="#7FA69B"; RED="#B42318"; AMBER="#9A4A0B"
FONT="Carlito" if any("Carlito" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams["font.family"]=FONT
OUT="/home/claude/figs/"

# ---------------- USE CASE ----------------
def stick(ax,x,y,name,s=0.32):
    ax.add_patch(Circle((x,y+0.55*s/0.32*0.32+0.35),0.16,fill=False,lw=1.6,ec=INK))
    ax.plot([x,x],[y+0.19,y-0.35],c=INK,lw=1.6)
    ax.plot([x-0.3,x+0.3],[y+0.02,y+0.02],c=INK,lw=1.6)
    ax.plot([x,x-0.25],[y-0.35,y-0.8],c=INK,lw=1.6); ax.plot([x,x+0.25],[y-0.35,y-0.8],c=INK,lw=1.6)
    ax.text(x,y-1.05,name,ha="center",va="top",fontsize=12,color=INK,fontweight="bold")
def sysactor(ax,x,y,name):
    ax.add_patch(FancyBboxPatch((x-0.95,y-0.42),1.9,0.84,boxstyle="round,pad=0.02",fc="white",ec=INK,lw=1.4))
    ax.text(x,y+0.12,"«system»",ha="center",fontsize=9,color="#56706A")
    ax.text(x,y-0.18,name,ha="center",fontsize=11,color=INK,fontweight="bold")
def usecase(ax,x,y,label,w=2.45,h=0.78):
    ax.add_patch(Ellipse((x,y),w,h,fc=MINT,ec=BRAND,lw=1.4))
    ax.text(x,y,label,ha="center",va="center",fontsize=10.5,color=INK,wrap=True)
def link(ax,p,q,style="-",label=None,arrow=False):
    if arrow:
        ax.annotate("",xy=q,xytext=p,arrowprops=dict(arrowstyle="->",ls="--",color=LINE,lw=1.2,shrinkA=0,shrinkB=0))
        mx,my=(p[0]+q[0])/2,(p[1]+q[1])/2
        ax.text(mx,my+0.12,label,fontsize=8.5,color="#56706A",ha="center",style="italic",bbox=dict(fc="white",ec="none",pad=0.5))
    else:
        ax.plot([p[0],q[0]],[p[1],q[1]],c="#4B6A63",lw=1.0)

def use_case():
    fig,ax=plt.subplots(figsize=(14,11.2)); ax.set_xlim(-0.2,14.2); ax.set_ylim(-0.4,11.0); ax.axis("off")
    ax.add_patch(Rectangle((2.55,0.25),8.95,9.35,fill=False,ec=INK,lw=1.8))
    ax.text(2.75,9.3,"SmartClinic+ system boundary",ha="left",fontsize=13,color=INK,fontweight="bold")
    U={}
    c1,c2,c3=4.05,7.0,9.95
    rows=[(c1,8.5,"View operational dashboard"),(c1,7.45,"View staffing forecast"),(c1,6.3,"Book appointment"),
          (c1,5.25,"View real-time availability"),(c1,4.2,"Reschedule or cancel"),(c1,3.15,"Earn loyalty rewards"),
          (c1,2.05,"Check in patient"),(c1,0.95,"Flag emergency"),
          (c2,8.5,"Send notifications"),(c2,6.3,"Authenticate user"),(c2,4.2,"Check allergy conflicts"),(c2,2.05,"Update smart queue"),
          (c3,8.5,"View doctor dashboard"),(c3,7.45,"Access patient EHR"),(c3,6.3,"Record consultation"),
          (c3,5.25,"Issue e-prescription"),(c3,4.05,"Assign task"),(c3,3.0,"Update task status"),(c3,1.95,"Record lab result"),
          (c3,0.95,"Call next patient")]
    for x,y,l in rows: usecase(ax,x,y,l); U[l]=(x,y)
    A={"Clinic Manager":(1.15,8.3),"Patient":(1.15,5.0),"Receptionist":(1.15,1.7),"Doctor":(12.95,7.0),"Nurse":(12.95,2.2)}
    for n,(x,y) in A.items(): stick(ax,x,y,n)
    sysactor(ax,7.0,10.35,"SMS / Email Gateway"); sysactor(ax,13.3,4.55,"Partner Pharmacy")
    E=lambda l,side: (U[l][0]+(1.22 if side=="r" else -1.22),U[l][1])
    for l in ["View operational dashboard","View staffing forecast"]: link(ax,(1.5,8.4),E(l,"l"))
    for l in ["Book appointment","View real-time availability","Reschedule or cancel","Earn loyalty rewards"]: link(ax,(1.5,5.1),E(l,"l"))
    for l in ["Check in patient","Book appointment"]: link(ax,(1.5,1.8),E(l,"l"))
    for l in ["View doctor dashboard","Access patient EHR","Record consultation","Issue e-prescription","Assign task","Call next patient"]: link(ax,(12.6,7.1),E(l,"r"))
    for l in ["Access patient EHR","Update task status","Record lab result"]: link(ax,(12.6,2.3),E(l,"r"))
    link(ax,(12.35,4.55),E("Issue e-prescription","r"))
    link(ax,(7.0,9.93),(7.0,8.89))
    link(ax,(c1,5.91),(c1,5.64),arrow=True,label="")
    ax.text(c1+0.1,5.78,"«include»",fontsize=8.5,color="#56706A",style="italic",ha="left",va="center")
    link(ax,(c1,7.84),(c1,8.11),arrow=True,label="")
    ax.text(c1+0.1,7.98,"«extend»",fontsize=8.5,color="#56706A",style="italic",ha="left",va="center")
    link(ax,(c1,1.34),(c1,1.66),arrow=True,label="")
    ax.text(c1+0.1,1.5,"«extend»",fontsize=8.5,color="#56706A",style="italic",ha="left",va="center")
    link(ax,(c1+1.1,6.55),(c2-0.95,8.2),arrow=True,label="«include»")
    link(ax,(c1+1.23,6.3),(c2-1.23,6.3),arrow=True,label="«include»")
    link(ax,(c3-1.23,7.4),(c2+0.9,6.55),arrow=True,label="«include»")
    link(ax,(c3-1.2,5.1),(c2+1.0,4.4),arrow=True,label="«include»")
    link(ax,(c1+1.23,2.05),(c2-1.23,2.05),arrow=True,label="«include»")
    link(ax,(c3-1.1,1.15),(c2+1.0,1.85),arrow=True,label="«include»")
    fig.savefig(OUT+"use_case.png",dpi=170,bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------------- SEQUENCE ----------------
def sequence(fname,parts,msgs,frags,title=None,width=15,step=0.62):
    n=len(parts); xs=[1.2+i*(width-2.4)/(n-1) for i in range(n)]
    X={p:x for p,x in zip(parts,xs)}
    total=sum(step*(1.35 if m[0]==m[1] else 1) for m in msgs)+0.9
    fig,ax=plt.subplots(figsize=(width,total*0.78+0.8)); ax.set_xlim(0,width); ax.set_ylim(-total,1.2); ax.axis("off")
    for p,x in X.items():
        ax.add_patch(FancyBboxPatch((x-0.95,0.2),1.9,0.72,boxstyle="round,pad=0.02",fc=BRAND,ec=BRAND))
        ax.text(x,0.56,p,ha="center",va="center",color="white",fontsize=11,fontweight="bold")
        ax.plot([x,x],[0.2,-total+0.3],ls=(0,(4,3)),c=LINE,lw=1)
    y=-0.55; ys=[]
    for i,(a,b,label,kind) in enumerate(msgs):
        ys.append(y)
        num=f"{i+1}. "
        if a==b:
            x=X[a]; ax.plot([x,x+0.55,x+0.55,x+0.08],[y,y,y-0.35,y-0.35],c=INK,lw=1.1)
            ax.annotate("",xy=(x+0.05,y-0.35),xytext=(x+0.2,y-0.35),arrowprops=dict(arrowstyle="-|>",color=INK,lw=1.1))
            ax.text(x+0.65,y-0.17,num+label,fontsize=10,color=INK,va="center")
            y-=step*1.35
        else:
            ls="--" if kind=="r" else "-"; col=RED if kind=="e" else INK
            ax.annotate("",xy=(X[b],y),xytext=(X[a],y),arrowprops=dict(arrowstyle="-|>" if kind!="r" else "->",ls=ls,color=col,lw=1.2))
            ax.text((X[a]+X[b])/2,y+0.09,num+label,fontsize=10,color=col,ha="center",va="bottom")
            y-=step
    for (i0,i1,guard,guard2,split) in frags:
        top=ys[i0]+0.42; bot=ys[i1]-0.3
        ax.add_patch(Rectangle((0.15,bot),width-0.3,top-bot,fill=False,ec=AMBER,lw=1.2))
        ax.add_patch(Rectangle((0.15,top-0.3),0.6,0.3,fc=AMBER,ec=AMBER)); ax.text(0.45,top-0.15,"alt",color="white",fontsize=9,ha="center",va="center",fontweight="bold")
        ax.text(0.85,top-0.15,guard,fontsize=9.5,color=AMBER,va="center",style="italic")
        if split is not None:
            sy=ys[split]+0.36; ax.plot([0.15,width-0.15],[sy,sy],ls=(0,(5,3)),c=AMBER,lw=1)
            ax.text(0.85,sy-0.16,guard2,fontsize=9.5,color=AMBER,va="center",style="italic")
    fig.savefig(OUT+fname,dpi=170,bbox_inches="tight",facecolor="white"); plt.close(fig)

def seqs():
    P=["Patient","Booking UI","BookingService","PostgreSQL","Notification outbox"]
    M=[("Patient","Booking UI","select doctor and day","s"),
       ("Booking UI","BookingService","available_slots(doctor, day)","s"),
       ("BookingService","PostgreSQL","SELECT active appointments","s"),
       ("PostgreSQL","BookingService","taken slots","r"),
       ("BookingService","Booking UI","free slots","r"),
       ("Patient","Booking UI","choose 09:00 and confirm","s"),
       ("Booking UI","BookingService","book(patient, doctor, slot)","s"),
       ("BookingService","BookingService","validate slot (future, hours, grid)","s"),
       ("BookingService","PostgreSQL","BEGIN (write lock)","s"),
       ("BookingService","PostgreSQL","check clash; INSERT appointment","s"),
       ("PostgreSQL","BookingService","row inserted (unique index satisfied)","r"),
       ("BookingService","Notification outbox","queue confirmation + 24 h reminder","s"),
       ("BookingService","PostgreSQL","COMMIT","s"),
       ("Booking UI","Patient","\"Appointment booked\"","r"),
       ("PostgreSQL","BookingService","IntegrityError (ux_active_slot)","e"),
       ("BookingService","PostgreSQL","ROLLBACK","s"),
       ("Booking UI","Patient","\"That slot has just been taken\"","e")]
    sequence("seq_booking.png",P,M,[(10,16,"[slot still free]","[concurrent request won the slot]",14)])
    P2=["Doctor","Record UI","RBAC guard","PrescriptionSvc","EHRService","PostgreSQL"]
    M2=[("Doctor","Record UI","submit medication, dosage, pharmacy","s"),
        ("Record UI","RBAC guard","requires(\"prescription:create\")","s"),
        ("RBAC guard","Record UI","authorised (role = doctor)","r"),
        ("Record UI","PrescriptionSvc","create(doctor, patient, med, dose)","s"),
        ("PrescriptionSvc","EHRService","allergies(patient)","s"),
        ("EHRService","PostgreSQL","SELECT allergies_enc","s"),
        ("PostgreSQL","EHRService","ciphertext","r"),
        ("EHRService","EHRService","Fernet decrypt","s"),
        ("EHRService","PrescriptionSvc","[\"penicillin\", \"latex\"]","r"),
        ("PrescriptionSvc","Record UI","AllergyConflict","e"),
        ("Record UI","Doctor","warning shown; nothing sent","e"),
        ("PrescriptionSvc","PostgreSQL","INSERT prescription + audit (RX_CREATE / RX_OVERRIDE)","s"),
        ("PrescriptionSvc","PostgreSQL","queue patient / pharmacy notification; COMMIT","s"),
        ("Record UI","Doctor","\"Prescription sent\"","r")]
    sequence("seq_prescription.png",P2,M2,[(9,13,"[allergy conflict and no override]","[no conflict, or justified override]",11)],width=16)

# ---------------- GANTT ----------------
def gantt():
    tasks=[("Sprint 1  Requirements, AHP, architecture, repo + CI",1,2,"Humayra / Maruf"),
           ("Sprint 2  Auth, RBAC, booking, concurrency control",3,4,"Mishkatul / Maruf"),
           ("Sprint 3  EHR, encryption, labs, doctor dashboard",5,6,"Maruf / Humayra"),
           ("Sprint 4  E-prescription, smart queue, notifications",7,8,"Humayra / Mukit / Mishkatul"),
           ("Sprint 5  Tasks, analytics, forecasting, loyalty",9,10,"Mukit / Humayra"),
           ("Sprint 6  System, security and user acceptance testing",11,12,"Mukit / all"),
           ("Continuous  unit tests, code review, CI on every PR",1,12,"all"),
           ("Deployment, training and handover",12,13,"Mishkatul / all")]
    fig,ax=plt.subplots(figsize=(13,4.9))
    for i,(n,s,e,o) in enumerate(tasks):
        c=LINE if n.startswith("Continuous") else (AMBER if n.startswith("Deploy") else BRAND)
        ax.barh(i,e-s+1,left=s-0.5,color=c,height=0.55)
        ax.text(e+0.6,i,o,va="center",fontsize=9.5,color="#56706A")
    for w,l in [(2.5,"M1 Requirements baseline"),(6.5,"M2 Core MVP"),(10.5,"M3 Feature complete"),(12.5,"M4 Go-live")]:
        ax.axvline(w,color=RED,lw=1,ls=":"); ax.text(w+0.08,-0.95,l,color=RED,fontsize=9,ha="left")
    ax.set_yticks(range(len(tasks))); ax.set_yticklabels([t[0] for t in tasks],fontsize=10.5,color=INK)
    ax.invert_yaxis(); ax.set_xticks(range(1,14)); ax.set_xticklabels([f"W{i}" for i in range(1,14)],fontsize=9.5)
    ax.set_xlim(0.4,16.3); ax.set_ylim(len(tasks)-0.4,-1.3)
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    ax.grid(axis="x",color="#E2ECE8"); ax.set_axisbelow(True)
    fig.savefig(OUT+"gantt.png",dpi=170,bbox_inches="tight",facecolor="white"); plt.close(fig)

use_case(); seqs(); gantt()
print("ok")

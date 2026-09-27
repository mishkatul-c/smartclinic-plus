import graphviz
F="Carlito"; INK="#17332E"; BRAND="#2E6B5E"; MINT="#EAF3F0"; LINE="#4B6A63"
def g(name, rankdir="TB", **kw):
    d=graphviz.Digraph(name, format="png", engine="dot")
    d.attr(rankdir=rankdir, fontname=F, bgcolor="white", dpi="170", nodesep="0.35", ranksep="0.5", **kw)
    d.attr("node", fontname=F, fontsize="12", color=BRAND, fontcolor=INK, style="rounded,filled", fillcolor=MINT, shape="box", penwidth="1.3")
    d.attr("edge", fontname=F, fontsize="10", color=LINE, fontcolor="#56706A", arrowsize="0.7")
    return d

# Architecture
a=g("architecture", compound="true")
with a.subgraph(name="cluster_c") as c:
    c.attr(label="Clients", fontname=F, fontcolor=INK, color="#C9D8D2", style="rounded")
    c.node("web","Patient web / mobile browser"); c.node("staff","Clinic workstation\n(doctor, nurse, reception, manager)")
with a.subgraph(name="cluster_p") as c:
    c.attr(label="Presentation layer  (Flask blueprints + Jinja templates)", fontname=F, fontcolor=INK, color="#C9D8D2", style="rounded")
    for n,l in [("r_auth","auth"),("r_pat","patient"),("r_cli","clinical"),("r_adm","admin")]: c.node(n,l)
with a.subgraph(name="cluster_x") as c:
    c.attr(label="Cross-cutting  (security.py)", fontname=F, fontcolor=INK, color="#C9D8D2", style="rounded")
    c.node("rbac","RBAC permission matrix\n+ CSRF + session auth", fillcolor="#FDECEA", color="#B42318")
    c.node("crypto","Field encryption\n(Fernet: AES + HMAC)", fillcolor="#FDECEA", color="#B42318")
with a.subgraph(name="cluster_s") as c:
    c.attr(label="Service layer  (business rules, transactions)", fontname=F, fontcolor=INK, color="#C9D8D2", style="rounded")
    for n,l in [("s_book","BookingService"),("s_q","QueueService"),("s_ehr","EHRService"),("s_rx","PrescriptionService"),
                ("s_lab","LabService"),("s_task","TaskService"),("s_an","AnalyticsService"),("s_eng","EngagementService"),("s_not","NotificationService")]:
        c.node(n,l)
with a.subgraph(name="cluster_d") as c:
    c.attr(label="Data layer", fontname=F, fontcolor=INK, color="#C9D8D2", style="rounded")
    c.node("db","PostgreSQL\n(ACID transactions, partial unique index,\naudit log, encrypted columns)", shape="cylinder", fillcolor="white")
    c.node("outbox","Notification outbox table", shape="cylinder", fillcolor="white")
a.node("gw","SMS / Email gateway", fillcolor="white", style="rounded,dashed")
a.node("ph","Partner pharmacy", fillcolor="white", style="rounded,dashed")
a.edge("web","r_pat",label=" HTTPS / TLS 1.3"); a.edge("staff","r_cli",label=" HTTPS"); a.edge("staff","r_adm")
a.edge("r_cli","s_ehr",lhead="cluster_s",ltail="cluster_p",label="  service calls")
a.edge("r_pat","rbac",style="dashed",arrowhead="none"); a.edge("s_ehr","crypto",style="dashed",arrowhead="none")
a.edge("s_rx","db",lhead="cluster_d",ltail="cluster_s",label="  SQL in transactions")
a.edge("outbox","gw",label=" scheduler"); a.edge("outbox","ph",label=" e-script")
a.render("/home/claude/figs/architecture", cleanup=True)

# ERD
e=graphviz.Digraph("erd", format="png", engine="dot")
e.attr(rankdir="TB", dpi="170", bgcolor="white", nodesep="0.25", ranksep="0.45", fontname=F)
e.attr("node", shape="plain", fontname=F); e.attr("edge", color=LINE, arrowhead="crow", arrowtail="tee", dir="both", fontname=F, fontsize="9")
def ent(n, cols):
    rows="".join(f'<tr><td align="left" port="{c.split()[0]}"><font point-size="10" color="{INK}">{c}</font></td></tr>' for c in cols)
    e.node(n, f'<<table border="1" cellborder="0" cellspacing="0" cellpadding="3" color="{BRAND}"><tr><td bgcolor="{BRAND}"><font color="white"><b>{n}</b></font></td></tr>{rows}</table>>')
ent("users",["id PK","email UNIQUE","full_name","phone","role","password_hash"])
ent("doctors",["user_id PK/FK","specialty","slot_minutes","day_start / day_end","running_delay"])
ent("appointments",["id PK","patient_id FK","doctor_id FK","slot_start","status","triage_level","checked_in_at / called_at","version","UX(doctor_id, slot_start) WHERE active"])
ent("health_records",["patient_id PK/FK","date_of_birth","medical_history_enc 🔒","allergies_enc 🔒"])
ent("consultations",["id PK","appointment_id FK","patient_id FK","doctor_id FK","diagnosis_enc 🔒","notes_enc 🔒"])
ent("prescriptions",["id PK","patient_id FK","doctor_id FK","medication","dosage","pharmacy","status"])
ent("lab_results",["id PK","patient_id FK","test_name","result_enc 🔒","flag","recorded_by FK"])
ent("tasks",["id PK","title","patient_id FK","assigned_to FK","created_by FK","status","due_at"])
ent("notifications",["id PK","user_id FK","channel","subject / body","send_after","sent_at"])
ent("loyalty_ledger",["id PK","patient_id FK","points","reason"])
ent("audit_log",["id PK","user_id","action","entity / entity_id","at"])
for a_,b_,ml in [("users","doctors",1),("users","health_records",1),("users","prescriptions",1),("users","lab_results",1),("users","tasks",1),
              ("doctors","appointments",1),("users","appointments",2),("appointments","consultations",1),
              ("users","notifications",2),("users","loyalty_ledger",2),("users","audit_log",2)]:
    e.edge(a_,b_,minlen=str(ml),**({"arrowhead":"tee"} if b_ in ("doctors","health_records") else {}))
e.render("/home/claude/figs/erd", cleanup=True)

# Git + CI workflow
c=g("cicd", rankdir="TB")
nodes=[("issue","Backlog item\n(GitHub Projects)"),("branch","feature/FR-xx branch"),("commit","Commits\n(conventional messages)"),("pr","Pull request\n+ DoD template"),
       ("ci","GitHub Actions CI\nflake8 → pytest → coverage ≥ 80%"),("rev","Code review\n(CODEOWNERS, 1 approval)"),("main","Merge to protected main"),("rel","Tagged release\nv0.x per sprint")]
for n,l in nodes: c.node(n,l)
with c.subgraph() as r: r.attr(rank="same"); [r.node(n) for n in ["issue","branch","commit","pr"]]
with c.subgraph() as r: r.attr(rank="same"); [r.node(n) for n in ["ci","rev","main","rel"]]
for x,y in [("issue","branch"),("branch","commit"),("commit","pr"),("ci","rev"),("rev","main"),("main","rel")]: c.edge(x,y)
c.edge("pr","ci")
c.edge("ci","commit",label=" fail → fix",style="dashed",color="#B42318",fontcolor="#B42318")
c.render("/home/claude/figs/cicd", cleanup=True)
print("ok")

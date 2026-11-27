"""Generate an editable, evidence-first academic presentation."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ROOT=Path(__file__).resolve().parents[1]
r=Presentation();r.slide_width=Inches(13.333);r.slide_height=Inches(7.5)
NAVY=RGBColor(11,23,42); DARK=RGBColor(20,38,61); WHITE=RGBColor(240,247,255)
MUTED=RGBColor(164,186,208); BLUE=RGBColor(81,155,232); GREEN=RGBColor(76,191,153)

def text(slide,x,y,w,h,message,size=23,color=WHITE,bold=False):
    box=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    f=box.text_frame;f.word_wrap=True
    for j,line in enumerate(message.split('\n')):
        p=f.paragraphs[0] if j==0 else f.add_paragraph()
        p.text=line;p.space_after=Pt(10);p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color
    return box

def slide(title,subtitle=None):
    s=r.slides.add_slide(r.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=NAVY
    rect=s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.6), Inches(.65), Inches(.09), Inches(.65));rect.fill.solid();rect.fill.fore_color.rgb=BLUE;rect.line.fill.background()
    text(s,.9,.68,11.7,.7,title,31,WHITE,True)
    if subtitle:text(s,.9,1.47,11.5,.5,subtitle,15,MUTED)
    text(s,.9,7.02,10,.25,'AI-HAS  |  Elective AI  |  Academic prototype — not production certified',9,MUTED)
    return s

def bullet(s,items,start=2.05,fontsize=20,gap=.84):
    for i,item in enumerate(items):
        y=start+i*gap
        text(s,1.0,y,.34,.4,'●',14,GREEN)
        text(s,1.45,y,10.8,.65,item,fontsize,WHITE)

s=slide('AI-HAS','AI-Powered Enterprise Helpdesk & Workflow Automation System')
text(s,1.0,2.5,11,1.0,'Evidence-first L1 IT support automation',36,WHITE,True)
text(s,1.0,4.0,11,1.8,'A bounded and auditable academic prototype featuring approved SOP retrieval, ticketing, controlled approvals and signed webhook integration.',24,MUTED)

s=slide('Problem and project objective')
bullet(s,['Repeated Level-1 support questions slow human service desks.','Unsupported AI responses and excessive automation can cause operational harm.','Goal: cite approved SOPs, create controlled tickets and escalate safely.','Do not claim real MTTR gains without operational baseline measurements.'])

s=slide('Requirements mapped to the rubric')
bullet(s,['AI/RAG architecture — 25%','Software engineering and workflow automation — 20%','Security and governance — 15%; evaluation and testing — 15%','Documentation — 15%; final presentation and defense — 10%'])

s=slide('End-to-end architecture')
bullet(s,['Browser (employee, agent, admin) → authenticated FastAPI endpoints','RAG layer → approved SOPs / optional OpenAI embeddings and ChromaDB','Operational SQLite → tickets, approvals, conversations, audit and event outbox','Action controller → validated tool call → signed webhook → sandbox receiver'])

s=slide('Three demonstrable workflows')
bullet(s,['Knowledge response: question → retrieved SOP → citation or refusal','Ticket flow: user request → validated persistent ticket → agent status history','Approval flow: immutable request → 24-hour gate → agent decision','Sandbox webhook: ticket event → signed HTTP → persisted notification'])

s=slide('RCTC and least-privilege control')
bullet(s,['Role: restricted Level-1 IT assistant, not an enterprise administrator','Context: authenticated requester and approved SOPs, not arbitrary web content','Task: answer, ticket, request approval, escalate, and record an audit event','Control: no secret disclosure, authorization bypass or direct privileged execution'])

s=slide('Executable evidence collected')
bullet(s,['41 local pytest tests passed — API, negative security and workflow checks','10 independent real-HTTP smoke checks passed — includes restart persistence','22/22 lexical retrieval sample cases — only 6 synthetic SOPs','Separate signed HTTP webhook integration passed — not n8n/Jira'])

s=slide('UI and evidence')
img=ROOT/'docs/evidence/v5-defense-screen-crop.png'
if img.exists():
    s.shapes.add_picture(str(img),Inches(1.0),Inches(1.82),width=Inches(8.2))
    text(s,9.5,2.0,2.8,3.4,'Captured v5 Chromium JavaScript test with a backend TestClient bridge.\n\nReal local HTTP testing is separate. Not proof of live AI.',17,MUTED)
else:bullet(s,['Frontend includes chat response with source ID and retrieval mode.','Use the live app to capture evidence on the defense environment.'])

s=slide('Faculty-feedback corrections in v5')
bullet(s,['Previously misleading free VPN answer now fails scope check with no false citation.','Unknown or unsupported requests offer explicit user-triggered agent escalation.','Escalation persists, is idempotent and appears in the actual agent queue.','Semantic indexing is chunked and version-aware; live provider verification pending.'],fontsize=19)

s=slide('Limitations and honest claims')
bullet(s,['OpenAI live model and ChromaDB embeddings: not verified without API access','Agentic tool schema is implemented; external model-driven action still needs proof','Password resets and software provisioning are simulated and approval gated','Production-grade SSO, backups, security review and cloud deployment remain out of scope'],fontsize=18)

s=slide('Live defense plan')
bullet(s,['Demonstrate an SOP question and unknown-question escalation.','Create a ticket; reload page; inspect agent queue and status history.','Show simulated approval and signed sandbox webhook delivery.','Run test suite and show genuine integration evidence with limitations.'])

s=slide('Conclusion')
text(s,1.0,2.3,11,1.3,'The defensible outcome is a controlled, integrated L1 helpdesk MVP.',32,WHITE,True)
text(s,1.0,4.1,11,1.8,'Production autonomy requires stronger identity, operational testing, real API verification and human oversight for privileged actions.',22,MUTED)

out=ROOT/'docs/AI-HAS_Defense_v5.pptx'
r.save(str(out))
print('Created',out, 'slides',len(r.slides))

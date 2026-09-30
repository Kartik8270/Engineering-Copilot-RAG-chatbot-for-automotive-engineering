"""Generate small sample engineering PDFs so you can demo the copilot immediately."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "sample_docs"
OUT.mkdir(exist_ok=True)
ss = getSampleStyleSheet()


def build(name, title, sections, table=None):
    story = [Paragraph(title, ss["Title"]), Spacer(1, 12)]
    for head, body in sections:
        story += [Paragraph(head, ss["Heading2"]), Paragraph(body, ss["BodyText"]), Spacer(1, 8)]
    if table:
        t = Table(table)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
        story.append(t)
    SimpleDocTemplate(str(OUT / name), pagesize=A4, title=title).build(story)


build("M-104_motor_vibration_report.pdf", "Project M-104 Incident Report",
      [("1 Summary", "Motor assembly M-104 showed excessive vibration above 3000 rpm during validation."),
       ("2 Symptoms", "Vibration amplitude exceeded 7 mm/s RMS. Audible whine and elevated bearing temperature."),
       ("3.2 Root Cause", "Teardown found bearing misalignment of 0.12 mm between the drive-end and "
        "non-drive-end housings. Vibration was caused by bearing misalignment."),
       ("4 Corrective Action", "Housing bores were re-machined and bearings realigned using a dial indicator.")])

build("M-087_rotor_report.pdf", "Project M-087 Troubleshooting Record",
      [("1 Summary", "Prototype M-087 exhibited excessive vibration at operating speed."),
       ("2 Investigation", "Bearing alignment and mounting were within tolerance."),
       ("3 Root Cause", "Dynamic balancing showed an imbalanced rotor, 14 g-mm residual imbalance, "
        "exceeding the G2.5 limit. Excessive vibration was associated with the imbalanced rotor."),
       ("4 Fix", "Rotor rebalanced by material removal; vibration dropped below 2 mm/s RMS.")])

build("M-121_bracket_change_report.pdf", "Project M-121 Design Change Review",
      [("1 Background", "Motor mounting bracket was lightened to reduce mass by 8 percent."),
       ("2.1 Post-Change Observations", "Vibration increased after the mounting bracket modification. "
        "Bracket stiffness fell and a resonance appeared near 410 Hz."),
       ("3 Resolution", "Added a gusset rib to restore stiffness; resonance moved above the operating range.")])

build("MAN-200_motor_service_manual.pdf", "MAN-200 Motor Service Manual",
      [("1 Scope", "Service procedures for the 48V traction motor family."),
       ("2 Fastener Torque", "Use the following torque values when reassembling the motor. Always use a calibrated wrench.")],
      table=[["Fastener", "Size", "Torque (N·m)"], ["End-cap bolt", "M8", "25"],
             ["Bearing housing bolt", "M10", "45"], ["Mounting bracket bolt", "M12", "70"]])
print("Sample PDFs written to", OUT)

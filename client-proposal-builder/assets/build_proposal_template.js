// ============================================================================
// Outbound Agency Proposal Build Template (docx-js)
// ----------------------------------------------------------------------------
// HOW TO USE:
//   1. Copy this file to your working directory as build_proposal.js
//   2. Fill in AGENCY constants (lines marked "// *** AGENCY ***") once
//   3. Fill in the CONTENT section below (search for "// === CONTENT ===")
//   4. Run: npm install docx --silent && node build_proposal.js
//   5. Output: <Prospect>_Proposal.docx in the current directory
//
// The helpers above the CONTENT section should rarely need changes — they
// encode the house style (Arial, navy headings, bordered tables with subtle
// shading, color-coded billable/non-billable). The CONTENT section is where
// you adapt for each prospect.
// ============================================================================

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageBreak,
} = require('docx');

// ----------------------------------------------------------------------------
// House style constants
// ----------------------------------------------------------------------------
const FONT = "Arial";
const CONTENT_WIDTH = 9360;          // US Letter, 1" margins (12240 - 2880)
const H1_COLOR = "1F3864";           // Deep navy
const H2_COLOR = "2E4F8A";           // Mid navy
const HEADER_SHADE = "E8EEF7";       // Pale blue (table headers)
const LABEL_SHADE = "F2F2F2";        // Pale gray (label cells)
const BILLABLE_SHADE = "E5F5E5";     // Pale green
const NON_BILLABLE_SHADE = "FBE5E5"; // Pale red

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// ----------------------------------------------------------------------------
// Paragraph helpers
// ----------------------------------------------------------------------------
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 300 },
    ...opts,
    children: opts.children || [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function pRich(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 300 },
    ...opts,
    children: runs,
  });
}

function bullet(text, runs) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80, line: 300 },
    children: runs || [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function boldLeadBullet(leadText, restText) {
  // For bullets with a bold lead-in like "Channel-fluent operators. Kevin..."
  return bullet(null, [
    new TextRun({ text: leadText, bold: true, font: FONT, size: 22 }),
    new TextRun({ text: restText, font: FONT, size: 22 }),
  ]);
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { after: 80, line: 300 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, bold: true, size: 32, font: FONT })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 26, font: FONT })],
  });
}

function blank() {
  return new Paragraph({ spacing: { after: 120 }, children: [new TextRun("")] });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

// ----------------------------------------------------------------------------
// Table helpers
// ----------------------------------------------------------------------------
function cell(text, opts = {}) {
  const {
    width, bold = false, align = AlignmentType.LEFT, shading,
    size = 22, paragraphs,
  } = opts;
  let children;
  if (paragraphs) {
    children = paragraphs;
  } else {
    children = [new Paragraph({
      alignment: align,
      spacing: { after: 60 },
      children: [new TextRun({ text, bold, font: FONT, size })],
    })];
  }
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: { top: 100, bottom: 100, left: 140, right: 140 },
    shading: shading ? { fill: shading, type: ShadingType.CLEAR } : undefined,
    verticalAlign: VerticalAlign.TOP,
    children,
  });
}

// Two-column label/value table (used for each pricing tier block)
function optionTable(rows, labelW = 2400) {
  const valueW = CONTENT_WIDTH - labelW;
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [labelW, valueW],
    rows: rows.map(([label, value]) => new TableRow({
      children: [
        cell(label, { width: labelW, bold: true, shading: LABEL_SHADE }),
        cell(value, { width: valueW }),
      ],
    })),
  });
}

// Generic header+rows table
function dataTable(columnWidths, header, rows) {
  return new Table({
    width: { size: columnWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: header.map((h, i) => cell(h, { width: columnWidths[i], bold: true, shading: HEADER_SHADE })),
      }),
      ...rows.map(r => new TableRow({
        children: r.map((c, i) => {
          // c can be a string OR { text, bold, align, shading }
          if (typeof c === 'string') return cell(c, { width: columnWidths[i] });
          return cell(c.text, { width: columnWidths[i], ...c });
        }),
      })),
    ],
  });
}

// ----------------------------------------------------------------------------
// === AGENCY CONSTANTS === Set these once for your agency
// ----------------------------------------------------------------------------

const AGENCY_NAME        = "[Your Agency Name]";               // *** AGENCY ***
const AGENCY_LEGAL_NAME  = "[Your Legal Entity Name]";         // *** AGENCY ***
const AGENCY_STATE       = "[State]";                          // *** AGENCY ***
const AGENCY_CONTACT_NAME= "[Your Name]";                      // *** AGENCY ***
const AGENCY_CONTACT_TITLE = "[Your Title]";                   // *** AGENCY ***
const AGENCY_CONTACT_EMAIL = "[your@email.com]";               // *** AGENCY ***

// ----------------------------------------------------------------------------
// === CONTENT === Adapt everything below for the prospect
// ----------------------------------------------------------------------------

const PROSPECT_NAME      = "[Prospect Legal Name]";            // legal name
const PROSPECT_CONTACT   = "[Prospect Contact Name]";          // primary signer
const PROSPECT_TITLE     = "[Prospect Title]";                 // title
const PROSPECT_URL       = "[https://prospectdomain.com/]";
const ENGAGEMENT_TITLE   = "Done-For-You Calling Engagement";
const ENGAGEMENT_SUBTITLE= "Completed-Conversations Outbound Program";
const PROPOSAL_DATE      = "[Month D, YYYY]";
const OUTPUT_FILENAME    = "[Prospect]_Proposal.docx";

const children = [];

// ----- Title block ----------------------------------------------------------
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "PROPOSAL", bold: true, size: 22, font: FONT })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new TextRun({ text: ENGAGEMENT_TITLE, bold: true, size: 40, font: FONT })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({ text: ENGAGEMENT_SUBTITLE, size: 26, font: FONT, italics: true })],
}));

// Prepared-for / Prepared-by side-by-side
children.push(new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: [4680, 4680],
  rows: [new TableRow({
    children: [
      new TableCell({
        borders: noBorders, width: { size: 4680, type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 0, right: 100 },
        children: [
          new Paragraph({ children: [new TextRun({ text: "PREPARED FOR", bold: true, size: 20, font: FONT, color: "6B6B6B" })], spacing: { after: 60 } }),
          new Paragraph({ children: [new TextRun({ text: PROSPECT_NAME, bold: true, size: 26, font: FONT })], spacing: { after: 40 } }),
          new Paragraph({ children: [new TextRun({ text: PROSPECT_CONTACT, size: 22, font: FONT })] }),
        ],
      }),
      new TableCell({
        borders: noBorders, width: { size: 4680, type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 100, right: 0 },
        children: [
          new Paragraph({ children: [new TextRun({ text: "PREPARED BY", bold: true, size: 20, font: FONT, color: "6B6B6B" })], spacing: { after: 60 } }),
          new Paragraph({ children: [new TextRun({ text: AGENCY_NAME, bold: true, size: 26, font: FONT })], spacing: { after: 40 } }),
          new Paragraph({ children: [new TextRun({ text: `${AGENCY_CONTACT_NAME} — ${AGENCY_CONTACT_EMAIL}`, size: 22, font: FONT })] }),
        ],
      }),
    ],
  })],
}));
children.push(new Paragraph({
  spacing: { before: 240, after: 240 },
  children: [new TextRun({ text: PROPOSAL_DATE, italics: true, size: 22, font: FONT, color: "6B6B6B" })],
}));

// ----- Executive Summary ----------------------------------------------------
children.push(h1("Executive Summary"));
children.push(p("[Paragraph 1: who the prospect is + 1-2 web-researched facts that ground credibility.]"));
children.push(p("[Paragraph 2: what the constraint actually is, reflecting their language. Pivot to what this proposal does.]"));
children.push(p("[Paragraph 3: tier summary + projected outcome in one sentence.]"));

// ----- Our Understanding ----------------------------------------------------
children.push(h1("Our Understanding of the Opportunity"));

children.push(h2(`What ${PROSPECT_NAME} Sells`));
children.push(p("[Describe the prospect's product or service using their language and economics from the call.]"));

children.push(h2("Why Pipeline Is the Bottleneck (Not the Offer)"));
children.push(p("[Name the underlying motion problem. If they referenced a bad experience by name (Branch, chop-shop, etc.), use it.]"));
children.push(p("The completed-conversations model inverts the incentive: callers are paid for meaningful, qualified dialogue with the right prospect, with meetings, activated leads, and nurtures all flowing out of that activity as natural byproducts."));

children.push(h2("Ideal Customer Profile"));
children.push(p("The pilot will be built around the prospect ICP. We will calibrate specifics in the Week-1 workshop, but the working profile is:"));
children.push(bullet("[Company-size, industry, technology, and revenue criteria.]"));
children.push(bullet("[Decision-maker titles.]"));
children.push(bullet("[Triggers we will sequence against — renewal windows, M&A, hiring, stack signals, etc.]"));

children.push(h2("Conversation Math"));
children.push(p("Working back from the deal economics, the completed-conversations model produces predictable pipeline once volume is held constant."));
children.push(dataTable(
  [2200, 2700, 1860, 2600],
  ["Conversations / Month", "Projected Meetings (10–15% set rate)", "Projected Show Rate", "Activated Leads Pool"],
  [
    ["50",  "5–7 / month (15–20 total)",   "~75%", "Continuous build into CRM"],
    ["100", "10–13 / month (30–40 total)", "~75%", "Continuous build into CRM"],
    // Add or remove rows to match tiers being offered
  ],
));
children.push(p("[Optional benchmark paragraph citing relevant proof points the user shared on the call — e.g., Workstreet 14% set rate, Ataxi 1,800 conversations → 500 activated leads.]"));

// ----- Proposed Engagement --------------------------------------------------
children.push(h1("Proposed Engagement"));
children.push(p(`A 90-day, fully-managed Done-For-You Calling program. ${AGENCY_NAME} supplies strategy, target list, dialing infrastructure, calling team, scripts, objection handling, dispositioning, and reporting. The Company supplies expertise, product context, and runs the meetings we book.`));

children.push(h2("Option A — 50 Completed Conversations / Month"));
children.push(optionTable([
  ["Duration",            "90 days"],
  ["Investment",          "$15,000 ($5,000 per month)"],
  ["Projected Meetings",  "15–20 booked discovery meetings over the term"],
  ["Activated Leads",     "Continuous handoff into the prospect's CRM"],
  ["What's Included",     "[Bulleted scope: dialing infrastructure, list, scripts, reporting, calendar handoff, weekly iteration.]"],
]));

children.push(blank());
children.push(h2("Option B — 100 Completed Conversations / Month"));
children.push(optionTable([
  ["Duration",            "90 days"],
  ["Investment",          "$30,000 ($10,000 per month)"],
  ["Projected Meetings",  "30–40 booked discovery meetings over the term"],
  ["Activated Leads",     "Continuous handoff into the prospect's CRM"],
  ["What's Included",     "[Everything in Option A at 2x volume + faster ICP iteration + dedicated weekly working session.]"],
]));

children.push(blank());
children.push(h2("Optional Add-Ons (for next-call discussion)"));
children.push(boldLeadBullet("Exclusivity / non-compete on calling territory. ",
  "[Defer to next call OR include hard exclusivity language as appropriate.]"));
children.push(boldLeadBullet("Per-conversation + revenue-share structure. ",
  "For proven offers where unit economics are well understood, we are open to a hybrid commercial model — a lower per-conversation rate paired with a back-end revenue share on closed deals. Best evaluated after the first 30–60 days of in-market data."));

// ----- How We Operate -------------------------------------------------------
children.push(h1("How We Operate"));
children.push(p("The pilot follows a four-phase cadence designed to move from zero to repeatable pipeline within 90 days."));

children.push(h2("Week 1 — Foundations"));
children.push(bullet("Kickoff and positioning workshop. Finalize ICP, disqualifiers, and territory rules."));
children.push(bullet("Build and enrich the target list."));
children.push(bullet("Set up dialing infrastructure, recording, and reporting cadence."));
children.push(bullet("Draft v1 scripts, dispositions, qualification criteria, and CRM routing."));

children.push(h2("Weeks 2–3 — Launch and Calibrate"));
children.push(bullet("Calling goes live at ramped volume. Daily call reviews against live dispositions."));
children.push(bullet("Rapid iteration on hooks, objections, and gatekeeper navigation."));
children.push(bullet("Calibration sync with the prospect on meeting quality and disposition accuracy."));

children.push(h2("Weeks 4–10 — Scale and Optimize"));
children.push(bullet("Sustained volume at the committed conversation tier."));
children.push(bullet("Weekly reporting on pipeline contribution — completed conversations, dispositions, meetings, show rate, activated leads."));
children.push(bullet("Expand into adjacent segments based on response and conversion data."));

children.push(h2("Weeks 11–12 — Results Review"));
children.push(bullet("Full pilot readout: completed conversations, meetings, show rate, opportunities, activated-lead pipeline."));
children.push(bullet("Recommendation on ongoing program structure, scale-up volume, and any commercial-model shifts."));
children.push(bullet("Playbook handoff: scripts, sequences, list logic, and reporting framework."));

// ----- Investment Summary ---------------------------------------------------
children.push(h1("Investment Summary"));
children.push(dataTable(
  [3000, 2000, 1480, 1480, 1400],
  ["Option", "Conv. / Month", "Monthly", "Months", "Total"],
  [
    ["Option A — Done-For-You Calling", { text: "50",  align: AlignmentType.RIGHT }, { text: "$5,000",  align: AlignmentType.RIGHT }, { text: "3", align: AlignmentType.RIGHT }, { text: "$15,000", align: AlignmentType.RIGHT, bold: true }],
    ["Option B — Done-For-You Calling", { text: "100", align: AlignmentType.RIGHT }, { text: "$10,000", align: AlignmentType.RIGHT }, { text: "3", align: AlignmentType.RIGHT }, { text: "$30,000", align: AlignmentType.RIGHT, bold: true }],
  ],
));

children.push(blank());
children.push(h2("Projected Outcomes"));
children.push(bullet("[Outcome bullets tied to each tier and any qualitative wins — playbook, ICP data, etc.]"));

children.push(h2("Payment Terms"));
children.push(bullet("Monthly invoicing."));
children.push(bullet("First month due on execution of this agreement to kick off list build, infrastructure setup, and Week-1 foundations."));
children.push(bullet("Month-to-month after the initial 90-day term, cancelable with 30 days' notice."));

// ----- Why [Agency] ---------------------------------------------------------
children.push(h1(`Why ${AGENCY_NAME}`));
children.push(p("[1-2 sentences on your agency's approach and what makes it distinct from generic outbound vendors. Lead with operator credibility, not sales language.]"));
children.push(h2(`What You Get With ${AGENCY_NAME}`));
children.push(boldLeadBullet("[Operator credibility hook]. ", "[Insert your team's relevant domain background. Tailor to the prospect's world — channel, SaaS, MSSP, DTC, etc.]"));
children.push(boldLeadBullet("Completed-conversations model. ", "We bill against quality conversations, not forced calendar bookings. Incentives line up with how good operators already think about top-of-funnel."));
children.push(boldLeadBullet("Custom dialing infrastructure. ", "AI-supported calling infrastructure produces 8–10x the conversation volume of traditional single-line SDR teams."));
children.push(boldLeadBullet("Activated-leads handoff. ", "Beyond booked meetings, we deliver every nurture, activated lead, and “interested but not now” prospect into your CRM — building a compounding prospecting list."));
children.push(boldLeadBullet("Meeting quality > meeting quantity. ", "Strict qualification against ICP before booking. No tire-kickers forced onto your calendar to hit a vendor quota."));

// ----- Terms and Conditions -------------------------------------------------
// In practice, build this section programmatically from the
// canonical assets/terms_and_conditions.md file (read it, parse the 23
// sections, emit each as a bold "N. Title" paragraph followed by body
// paragraphs). For brevity in this template, see how the Bridgepointe build
// did it via repeated calls to a `termsSection(num, title, paragraphs)`
// helper. Always include all 23 sections — the legal tail is non-negotiable.

children.push(pageBreak());
children.push(h1("Terms and Conditions"));
children.push(p("[Read assets/terms_and_conditions.md and emit all 23 sections here, swapping {COMPANY} → \"" + PROSPECT_NAME + "\". Each section: bold heading like \"1. Services\" followed by body paragraphs. Use bullets for §5 (Termination) sub-points and for §3(a)-(d) sub-headings.]"));

// ----- Next Steps + Acceptance ----------------------------------------------
children.push(pageBreak());
children.push(h1("Next Steps"));
children.push(numbered("Countersign this proposal (see acceptance block below), designating the selected option."));
children.push(numbered(`First invoice issued and paid; ${AGENCY_NAME} begins infrastructure build and list work the same day.`));
children.push(numbered("60-minute kickoff within 3 business days of execution."));
children.push(numbered("Calls live by end of Week 1; first completed conversations and activated leads inside CRM by end of Week 2."));

children.push(h2("Acceptance"));
children.push(p(`By signing below, the parties agree to be bound by the terms of this proposal, including the Scope of Services, Investment Summary, and Terms and Conditions set forth herein. This document constitutes the entire Agreement between ${PROSPECT_NAME} and ${AGENCY_LEGAL_NAME} for the 90-day ${ENGAGEMENT_TITLE.toLowerCase()} at the option and total investment designated below, and shall become effective upon the date of last signature below (the “Effective Date”).`));

children.push(pRich([new TextRun({ text: "Selected Option:", bold: true, font: FONT, size: 22 })], { spacing: { before: 160, after: 100 } }));
children.push(p("☐  Option A — 50 Completed Conversations / Month — $5,000/mo — $15,000 total"));
children.push(p("☐  Option B — 100 Completed Conversations / Month — $10,000/mo — $30,000 total"));

// Signature block table
children.push(blank());
const sigCols = [4680, 4680];
children.push(new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: sigCols,
  rows: [
    new TableRow({
      children: [
        cell("FOR THE COMPANY (Client)", { width: sigCols[0], bold: true, shading: LABEL_SHADE }),
        cell("FOR THE SERVICE PROVIDER",  { width: sigCols[1], bold: true, shading: LABEL_SHADE }),
      ],
    }),
    new TableRow({
      children: [
        new TableCell({
          borders, width: { size: sigCols[0], type: WidthType.DXA },
          margins: { top: 100, bottom: 100, left: 140, right: 140 },
          children: [
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: PROSPECT_NAME, bold: true, font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: PROSPECT_URL, font: FONT, size: 20, color: "555555" })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Signature: ____________________________", font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: `Name: ${PROSPECT_CONTACT}`, font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: `Title: ${PROSPECT_TITLE}`, font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Date: __________________________", font: FONT, size: 22 })] }),
          ],
        }),
        new TableCell({
          borders, width: { size: sigCols[1], type: WidthType.DXA },
          margins: { top: 100, bottom: 100, left: 140, right: 140 },
          children: [
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: AGENCY_LEGAL_NAME, bold: true, font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: `A ${AGENCY_STATE} Company`, font: FONT, size: 20, color: "555555" })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Signature: ____________________________", font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: `Name: ${AGENCY_CONTACT_NAME}`, font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: `Title: ${AGENCY_CONTACT_TITLE}`, font: FONT, size: 22 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Date: __________________________", font: FONT, size: 22 })] }),
          ],
        }),
      ],
    }),
  ],
}));

// ----- Appendix A — Completed Conversation Criteria -------------------------
children.push(pageBreak());
children.push(h1("Appendix A — Completed Conversation Criteria"));
children.push(p("This Appendix defines the term “Completed Conversation” as used in this Agreement for purposes of reporting and performance measurement."));

children.push(h2("Definition of Conversation"));
children.push(p("A “Conversation” is an interaction where the prospect and the representative engage in meaningful dialogue. Meaningful does not always mean the outcome is favorable; however, the outcome of the call must be clear. The prospect must have an understanding of what the Service Provider does during the call."));

children.push(h2("Billing and Disposition Rules"));
children.push(bullet("Each interaction is assigned an outcome label (a “Disposition”) that indicates what happened on the call."));
children.push(bullet("Each prospect has a soft cap of three (3) billable Dispositions."));
children.push(bullet("Billable Conversations may only be billed once per prospect, per Disposition type."));
children.push(bullet("A call dispositioned the same way twice for the same prospect is a “Double Disposition”; only the first instance is billable."));
children.push(bullet("Example: A prospect may be billed for both a “Meeting Scheduled” and a subsequent “Reschedule,” but not for two “Reschedules.”"));

// Billable dispositions table
children.push(h2("Billable Dispositions"));
const dispCols = [1900, 1100, 6360];
function dispRow(name, status, def, shade) {
  return [
    { text: name, bold: true },
    { text: status, bold: true, align: AlignmentType.CENTER, shading: shade },
    def,
  ];
}
children.push(dataTable(
  dispCols,
  ["Disposition", "Status", "Definition and Requirements"],
  [
    dispRow("Meeting Scheduled",  "Billable", "The prospect understood what the Service Provider does and agreed to speak again at a specific date and time. A new meeting is created and added to the calendar. Requirements: The prospect must hear enough of the pitch to understand what the Service Provider does. The prospect must agree to a specific day and time for a meeting. A calendar invite must be sent on or immediately after the call ends.", BILLABLE_SHADE),
    dispRow("Meeting Confirmed",  "Billable", "A meeting was already scheduled prior to the call. During the call, the prospect confirmed by phone that they still plan to attend. No new meeting is created; the call exists solely to ensure the meeting occurs. Requirements: A meeting with the prospect must already exist and be pending attendance. A reminder must be given to the prospect of the upcoming date and time. The prospect must confirm that they will be attending.", BILLABLE_SHADE),
    dispRow("Reschedule",         "Billable", "A meeting already existed but the prospect could not attend at the original time. During the call, a new date or time is agreed upon, and the old meeting is replaced. Requirements: A meeting with the prospect must already exist or have been no-showed. The prospect must agree to a specific day and time for a new meeting. A calendar invite must be sent on or immediately after the call ends.", BILLABLE_SHADE),
    dispRow("Activated Lead",     "Billable", "The prospect is interested and understands what the Service Provider does, but is not ready to schedule a meeting at the present time. Follow-up is expected to occur within one to two weeks. Requirements: The prospect must hear enough of the pitch to understand what the Service Provider does. The prospect must respond with a willingness to learn more. The follow-up process should take place within one month of the initial call.", BILLABLE_SHADE),
    dispRow("Nurture",            "Billable", "The prospect is interested and understands the offer, but the timing is not right (e.g., “maybe later,” “in a few months,” or “not this year”). Follow-up occurs on a longer horizon. Requirements: The prospect must hear enough of the pitch to understand what the Service Provider does. The prospect must respond with a willingness to learn more. The follow-up process should take place beyond one month of the initial call.", BILLABLE_SHADE),
    dispRow("Not Interested",     "Billable", "The prospect heard and understood the pitch but clearly declined. No follow-up is needed. Requirements: The prospect must hear enough of the pitch to understand what the Service Provider does. The prospect must respond with zero willingness to learn more. An attempt should be made to understand the prospect’s reasoning.", BILLABLE_SHADE),
    dispRow("Referred Outward",   "Billable", "The person who answered is not the correct contact but clearly identified the correct person. They heard the pitch and pointed the representative to the right individual, who is then added to the list if possible. Requirements: The prospect must hear enough of the pitch to understand what the Service Provider does. The prospect must relay that they are not the right person at their company. The prospect must provide a referral, preferably including a phone number.", BILLABLE_SHADE),
    dispRow("Not Me",             "Billable", "The person who answered is not the correct contact. They work at the company and heard the pitch, but cannot or will not share information or make a referral. The call reached a real person, but not the right one. Requirements: The prospect must hear enough of the pitch to understand what the Service Provider does. The prospect must relay that they are not the right person at their company. The prospect must deny giving a referral after the representative asks for one.", BILLABLE_SHADE),
  ],
));

children.push(blank());
children.push(h2("Non-Billable Dispositions"));
children.push(dataTable(
  dispCols,
  ["Disposition", "Status", "Definition and Requirements"],
  [
    dispRow("Connect Incomplete", "Not Billable", "The call ended before the pitch could be delivered. The prospect did not fully hear or understand what the Service Provider does (e.g., dropped call, early hang-up, interruption). Requirements: The prospect did not hear enough of the pitch to understand what the Service Provider does.", NON_BILLABLE_SHADE),
    dispRow("Left Voicemail",     "Not Billable", "The call reached voicemail and a message was left. No live conversation occurred. Requirements: A voicemail was left for the prospect.", NON_BILLABLE_SHADE),
    dispRow("Wrong Number",       "Not Billable", "The phone number is incorrect or no longer belongs to the intended person or company. Requirements: The number called was completely wrong.", NON_BILLABLE_SHADE),
    dispRow("Bad Data",           "Not Billable", "The information in the system is wrong — wrong name, title, company, or industry. The lead itself is inaccurate. Requirements: The prospect’s data is so incorrect that the representative cannot pitch or retrieve value.", NON_BILLABLE_SHADE),
    dispRow("Not In Swimlane",    "Not Billable", "Right person, wrong business for what the Service Provider has to offer. Requirements: The prospect’s data is correct, but the prospect would be of no use to the offer.", NON_BILLABLE_SHADE),
    dispRow("No Answer",          "Not Billable", "No real person answered the call — it may ring with no response, go to an automated system, or connect to a robot or incorrect line. Requirements: The call was picked up, but no one was on the other line.", NON_BILLABLE_SHADE),
    dispRow("Gatekeeper",         "Not Billable", "Someone who controls access to the decision-maker answered and blocked the call. The pitch did not reach the intended prospect. Requirements: A gatekeeper picked up instead and the representative cannot pitch or retrieve value.", NON_BILLABLE_SHADE),
    dispRow("DNC",                "Not Billable", "The person clearly asked to be removed from calling. This must be respected by law; no further calls are allowed under any circumstance. Requirements: The prospect did not want to learn more and asked to not be called again.", NON_BILLABLE_SHADE),
  ],
));

// ----------------------------------------------------------------------------
// Assemble + write
// ----------------------------------------------------------------------------
const doc = new Document({
  creator: AGENCY_NAME,
  title: `${PROSPECT_NAME} — ${AGENCY_NAME} Proposal`,
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: H1_COLOR },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: H2_COLOR },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children,
  }],
});

const outPath = path.join(__dirname, OUTPUT_FILENAME);
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("Wrote", outPath, "size:", buffer.length, "bytes");
}).catch(e => { console.error(e); process.exit(1); });

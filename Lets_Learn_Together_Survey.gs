/**
 * 🌈 Let's Learn Together! – ISL STEM Bridge student activity
 * RV College of Engineering – Social Development Experiential Learning
 *
 * HOW IT WORKS
 *   Run createLetsLearnTogether() once. It creates:
 *     1. A friendly Google Form (anonymous, no sign-in, every question optional)
 *     2. A linked Google Sheet that stores every answer ("Responses" tab)
 *     3. A "Summary" tab that counts the answers automatically
 *
 *   Running it again will NOT create a second form. It only prints the links again.
 *
 * WHAT APPS SCRIPT CANNOT DO (Google limitation)
 *   Apps Script cannot change a form's colours, fonts, text size or header picture.
 *   Set those by hand in the form editor: 🎨 Customize theme (see the instructions).
 *   Pictures CAN be added by the script – paste image links into IMAGES below (optional).
 */

const FORM_TITLE = "🌈 Let's Learn Together!";
const FORM_DESCRIPTION = [
  '✨ Your Ideas Matter! ✨',
  '',
  'Hello! 👋',
  'We want to know how you enjoy learning Science, Maths and Computers.',
  'Pick the answers you like. There are no right or wrong answers!',
  'Your ideas will help us make learning resources more interesting and accessible.',
  '',
  '🔬 📚 💻 🪐 🌱',
  '',
  '• Taking part is your choice.',
  '• You can skip any question or stop at any time.',
  '• We do not ask your name. Nobody will know which answers are yours.',
  '• Your answers are for a college project at RV College of Engineering.',
  '',
  'Thank you for helping us! 💛',
].join('\n');
const SHEET_TITLE = "Let's Learn Together – Student Responses";
const RESPONSES_SHEET = 'Responses';
const SUMMARY_SHEET = 'Summary';

// OPTIONAL PICTURES
// Paste a direct link to a PNG or JPG you are allowed to use (for example, your own Canva drawing
// shared publicly). Leave as '' to skip. A broken link is skipped – it never stops the script.
const IMAGES = {
  header: '', // welcome picture, e.g. children learning together
  q1: '', // school
  q2: '', // science / maths / computers
  q3: '', // helping hands
  q4: '', // videos, pictures, books
  q5: '', // microscope or dictionary
  q6: '', // stars / rocket
};

// Each question gets its own fun "page" with a small title, like a magazine section.
const QUESTIONS = [
  {
    key: 'q1',
    page: '🏫 About You',
    title: '1. Which class are you studying in?',
    choices: ['Class 1–5', 'Class 6–7', 'Class 8–10', 'Class 11–12', 'Other'],
  },
  {
    key: 'q2',
    page: '💖 Your Favourite',
    title: '2. Which subject do you LOVE?',
    choices: ['🔬 Science', '🔢 Mathematics', '💻 Computers', '📚 Other'],
  },
  {
    key: 'q3',
    page: '🤝 A Little Help',
    title: '3. Which subject would you like more help learning?',
    choices: ['Science', 'Mathematics', 'Computers', 'None at the moment'],
  },
  {
    key: 'q4',
    page: '🎨 Your Learning Style',
    title: '4. How do you LIKE learning new things?',
    choices: [
      '🤟 ISL videos',
      '🖼️ Pictures and diagrams',
      '🎬 Animated videos',
      '📖 Written explanations',
      '👩‍🏫 Teacher explanations',
      'A combination of these',
    ],
  },
  {
    key: 'q5',
    page: '🔤 New Science Words',
    title: '5. How do you usually learn a NEW scientific word?',
    choices: [
      'My teacher explains its meaning.',
      'I learn its ISL sign.',
      'I look at pictures or diagrams.',
      'I watch an educational video.',
      'I read its meaning.',
      'Other ways.',
    ],
  },
  {
    key: 'q6',
    page: '🚀 Imagine This!',
    title: '6. Imagine learning with ISL videos, pictures and animations together. Which would you prefer?',
    help: 'Every answer is helpful. Pick the one that is true for you.',
    choices: ['🌟 I would love to try it!', '😊 Maybe!', 'I prefer my current learning method.'],
  },
];

/** MAIN FUNCTION – run this one. Safe to run again: it never makes a duplicate. */
function createLetsLearnTogether() {
  const props = PropertiesService.getScriptProperties();

  // 1. Stop if this script already made the form.
  const savedFormId = props.getProperty('LLT_FORM_ID');
  if (savedFormId) {
    try {
      const form = FormApp.openById(savedFormId);
      Logger.log('✅ The form already exists. No new form was created.');
      logLinks_(form);
      return;
    } catch (e) {
      Logger.log('The saved form could not be opened (it may have been deleted). Creating a new one...');
    }
  }

  // 2. Create the form and remember it straight away, so a crash later can't cause a duplicate.
  const form = FormApp.create(FORM_TITLE);
  props.setProperty('LLT_FORM_ID', form.getId());

  form
    .setDescription(FORM_DESCRIPTION)
    .setCollectEmail(false) // no email addresses
    .setLimitOneResponsePerUser(false) // true would force Google sign-in
    .setAllowResponseEdits(false)
    .setPublishingSummary(false) // students cannot see other students' answers
    .setShowLinkToRespondAgain(true) // the next student on a shared tablet can start fresh
    .setProgressBar(true)
    .setConfirmationMessage(
      '🎉 Thank you for learning with us!\n\nYour ideas will help make learning more fun for everyone. 🌈'
    );

  tryStep_(() => form.setEmailCollectionType(FormApp.EmailCollectionType.DO_NOT_COLLECT), 'email collection setting');
  tryStep_(() => form.setRequireLogin(false), 'sign-in setting (only exists for school/work Google accounts)');

  // 3. Welcome picture (optional), then one question per page.
  addImage_(form, IMAGES.header, 'Welcome picture');

  QUESTIONS.forEach((q, i) => {
    form.addPageBreakItem()
      .setTitle(q.page)
      .setHelpText(`Question ${i + 1} of ${QUESTIONS.length}`);
    addImage_(form, IMAGES[q.key], q.page);
    form.addMultipleChoiceItem()
      .setTitle(q.title)
      .setHelpText(q.help || 'Pick one answer. You can skip this if you want.')
      .setChoiceValues(q.choices)
      .setRequired(false);
  });

  tryStep_(() => form.setPublished(true), 'publish setting');
  form.setAcceptingResponses(true);

  // 4. Create the linked spreadsheet.
  const ss = SpreadsheetApp.create(SHEET_TITLE);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  setUpSpreadsheet_(ss.getId());

  Logger.log("🎉 Let's Learn Together! was created successfully.");
  logLinks_(form);
}

/** Prints the three links again. */
function showLinks() {
  const id = PropertiesService.getScriptProperties().getProperty('LLT_FORM_ID');
  if (!id) {
    Logger.log('No form yet. Run createLetsLearnTogether() first.');
    return;
  }
  logLinks_(FormApp.openById(id));
}

/**
 * Makes the script "forget" the current form, so the NEXT run makes a brand-new one.
 * It does NOT delete the old form or spreadsheet – delete those from Google Drive yourself if needed.
 */
function resetSetup() {
  PropertiesService.getScriptProperties().deleteProperty('LLT_FORM_ID');
  Logger.log('Reset done. The next run of createLetsLearnTogether() will create a NEW form.');
}

// ---------- helpers ----------

function addImage_(form, url, altText) {
  if (!url) return;
  try {
    const blob = UrlFetchApp.fetch(url).getBlob();
    form.addImageItem().setImage(blob).setTitle('').setHelpText('').setAlignment(FormApp.Alignment.CENTER);
    Logger.log('Added picture: ' + altText);
  } catch (e) {
    Logger.log('Note: skipped picture "' + altText + '" – ' + e.message);
  }
}

function setUpSpreadsheet_(ssId) {
  // Google needs a moment to add the response tab after linking.
  let ss, responses;
  for (let attempt = 0; attempt < 10 && !responses; attempt++) {
    SpreadsheetApp.flush();
    ss = SpreadsheetApp.openById(ssId);
    responses = ss.getSheets().find((s) => s.getFormUrl());
    if (!responses) Utilities.sleep(1000);
  }
  if (!responses) {
    Logger.log('Note: the response tab is not ready yet. Answers will still be saved; the Summary tab was skipped.');
    return;
  }

  // Tidy the responses tab (renaming it does not break the link to the form).
  responses.setName(RESPONSES_SHEET);
  responses.setFrozenRows(1);
  responses.getRange(1, 1, 1, QUESTIONS.length + 1)
    .setFontWeight('bold')
    .setBackground('#E1D5F5')
    .setWrap(true);
  responses.setColumnWidths(2, QUESTIONS.length, 230);

  // Remove the empty default tab ("Sheet1").
  ss.getSheets().forEach((s) => {
    if (s.getSheetId() !== responses.getSheetId()) ss.deleteSheet(s);
  });

  // Summary tab: counts and percentages that update by themselves.
  const summary = ss.insertSheet(SUMMARY_SHEET);
  const ref = `'${RESPONSES_SHEET}'!`;
  const rows = [['Total responses', `=COUNTA(${ref}A2:A)`, ''], ['', '', '']];
  const headerRows = [];

  QUESTIONS.forEach((q, i) => {
    const col = String.fromCharCode(66 + i); // column A = Timestamp, B = Question 1, C = Question 2 ...
    headerRows.push(rows.length + 1);
    rows.push([q.title, 'Count', '% of students']);
    q.choices.forEach((choice) => {
      const r = rows.length + 1;
      rows.push([choice, `=COUNTIF(${ref}${col}2:${col}, "${choice}")`, `=IF($B$1=0, 0, B${r}/$B$1)`]);
    });
    const skipRow = rows.length + 1;
    rows.push([
      '(skipped this question)',
      `=$B$1-SUM(B${skipRow - q.choices.length}:B${skipRow - 1})`,
      `=IF($B$1=0, 0, B${skipRow}/$B$1)`,
    ]);
    rows.push(['', '', '']);
  });

  summary.getRange(1, 1, rows.length, 3).setValues(rows);
  summary.getRange(1, 1, 1, 2).setFontWeight('bold').setBackground('#C8E6C9');
  summary.getRange(1, 3, rows.length, 1).setNumberFormat('0%');
  headerRows.forEach((r) => summary.getRange(r, 1, 1, 3).setFontWeight('bold').setBackground('#BBDEFB'));
  summary.setColumnWidth(1, 460);
  summary.setColumnWidths(2, 2, 110);
}

function logLinks_(form) {
  let studentLink = form.getPublishedUrl();
  try {
    studentLink = form.shortenFormUrl(studentLink);
  } catch (e) {
    // the long link works fine too
  }
  let sheetLink = 'not linked';
  try {
    sheetLink = SpreadsheetApp.openById(form.getDestinationId()).getUrl();
  } catch (e) {
    // spreadsheet missing or not linked
  }
  Logger.log('👩‍🎓 STUDENT LINK (share this): ' + studentLink);
  Logger.log('✏️ EDIT LINK (your team only):  ' + form.getEditUrl());
  Logger.log('📊 RESPONSES SPREADSHEET:       ' + sheetLink);
}

function tryStep_(fn, what) {
  try {
    fn();
  } catch (e) {
    Logger.log('Note: skipped ' + what + ' – ' + e.message);
  }
}

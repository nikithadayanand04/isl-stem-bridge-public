/**
 * ISL STEM Bridge – Student Learning Survey
 * RV College of Engineering – Experiential Learning
 *
 * HOW IT WORKS
 *   Run createSurvey() once. It creates:
 *     1. A Google Form for students (anonymous, no sign-in, all questions optional)
 *     2. A linked Google Sheet that stores every response ("Responses" tab)
 *     3. A "Summary" tab that counts the answers automatically
 *
 *   Running createSurvey() again will NOT create a second form.
 *   It only prints the links to the form that already exists.
 */

const FORM_TITLE = 'Help Us Make Learning Easier!';
const FORM_DESCRIPTION =
  'We want to understand how you learn Science, Maths and Technology. ' +
  'There are no right or wrong answers. Your answers are anonymous and will help us improve our project.\n\n' +
  'You can skip any question. 🙂';
const SHEET_TITLE = 'ISL STEM Bridge – Student Survey Responses';
const RESPONSES_SHEET = 'Responses';
const SUMMARY_SHEET = 'Summary';

// type 'one'  = student picks one answer (round buttons)
// type 'many' = student can pick more than one answer (tick boxes)
const QUESTIONS = [
  {
    title: '🏫 1. Which class are you studying in?',
    type: 'one',
    choices: ['Class 1–5', 'Class 6–7', 'Class 8–10', 'Class 11–12', 'College'],
  },
  {
    title: '⭐ 2. Which subject do you like the most?',
    type: 'one',
    choices: ['Science', 'Mathematics', 'Computer / Technology', 'Other'],
  },
  {
    title: '🤔 3. Which subject is difficult for you?',
    type: 'one',
    choices: ['Science', 'Mathematics', 'Computer / Technology', 'None'],
  },
  {
    title: '💡 4. What helps you understand a new topic?',
    type: 'many',
    choices: ['ISL videos', 'Pictures and diagrams', 'Animations and videos', 'Written explanations', 'Teacher explaining'],
  },
  {
    title: '🔬 5. What happens when you find a difficult scientific word?',
    type: 'many',
    choices: [
      'Teacher explains it',
      'Teacher shows a picture',
      'The word is fingerspelled',
      'I search for its sign',
      'I find it difficult to understand',
    ],
  },
  {
    title: '🤟 6. Are scientific words sometimes difficult because you cannot find their ISL signs?',
    type: 'one',
    choices: ['Often', 'Sometimes', 'Never', 'Not sure'],
  },
  {
    title: '🎬 7. Would you like to learn difficult topics using ISL, pictures and animations together?',
    type: 'one',
    choices: ['Yes', 'Maybe', 'No'],
  },
  {
    title: '🚀 8. What would help you learn better?',
    type: 'one',
    choices: ['More ISL videos', 'More pictures and animations', 'Simple explanations', 'More examples', 'All of these'],
  },
];

/** MAIN FUNCTION – run this one. Safe to run again: it never makes a duplicate. */
function createSurvey() {
  const props = PropertiesService.getScriptProperties();

  // 1. Stop if a form was already made by this script.
  const savedFormId = props.getProperty('FORM_ID');
  if (savedFormId) {
    try {
      const form = FormApp.openById(savedFormId);
      Logger.log('✅ The survey already exists. No new form was created.');
      logLinks_(form);
      return;
    } catch (e) {
      Logger.log('The saved form could not be opened (it may have been deleted). Creating a new one...');
    }
  }

  // 2. Create the form and remember it straight away, so a crash later can't cause a duplicate.
  const form = FormApp.create(FORM_TITLE);
  props.setProperty('FORM_ID', form.getId());

  form
    .setDescription(FORM_DESCRIPTION)
    .setCollectEmail(false) // no email addresses
    .setLimitOneResponsePerUser(false) // true would force Google sign-in
    .setAllowResponseEdits(false)
    .setPublishingSummary(false) // students cannot see other students' answers
    .setShowLinkToRespondAgain(true) // the next student on a shared device can start fresh
    .setProgressBar(true)
    .setConfirmationMessage('Thank you! 🎉 Your answers will help us make learning easier.');

  tryStep_(() => form.setEmailCollectionType(FormApp.EmailCollectionType.DO_NOT_COLLECT), 'email collection setting');
  tryStep_(() => form.setRequireLogin(false), 'sign-in setting (only exists for school/work Google accounts)');

  // 3. Add the questions – one per page so it never feels crowded.
  QUESTIONS.forEach((q, i) => {
    if (i > 0) form.addPageBreakItem();
    const item = q.type === 'many' ? form.addCheckboxItem() : form.addMultipleChoiceItem();
    item
      .setTitle(q.title)
      .setHelpText(q.type === 'many' ? 'You can choose more than one.' : 'Choose one.')
      .setChoiceValues(q.choices)
      .setRequired(false);
  });

  tryStep_(() => form.setPublished(true), 'publish setting');
  form.setAcceptingResponses(true);

  // 4. Create the linked spreadsheet.
  const ss = SpreadsheetApp.create(SHEET_TITLE);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  setUpSpreadsheet_(ss.getId());

  Logger.log('🎉 Survey created successfully!');
  logLinks_(form);
}

/** Prints the three links in the Execution log. Run on its own any time you need the links. */
function showLinks() {
  const id = PropertiesService.getScriptProperties().getProperty('FORM_ID');
  if (!id) {
    Logger.log('No survey yet. Run createSurvey() first.');
    return;
  }
  logLinks_(FormApp.openById(id));
}

/**
 * Makes the script "forget" the current form, so the NEXT createSurvey() run makes a brand-new one.
 * It does NOT delete the old form or spreadsheet – delete those from Google Drive yourself if needed.
 */
function resetSetup() {
  PropertiesService.getScriptProperties().deleteProperty('FORM_ID');
  Logger.log('Reset done. The next run of createSurvey() will create a NEW form.');
}

// ---------- helpers ----------

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
    Logger.log('Note: the response tab is not ready yet. Responses will still be saved; the Summary tab was skipped.');
    return;
  }

  // Tidy the responses tab (renaming it does not break the link to the form).
  responses.setName(RESPONSES_SHEET);
  responses.setFrozenRows(1);
  responses.getRange(1, 1, 1, QUESTIONS.length + 1)
    .setFontWeight('bold')
    .setBackground('#FFE599')
    .setWrap(true);
  responses.setColumnWidths(2, QUESTIONS.length, 220);

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
    rows.push([q.title + (q.type === 'many' ? '  (more than one answer allowed)' : ''), 'Count', '% of students']);
    q.choices.forEach((choice) => {
      // Tick-box answers are stored together in one cell ("A, B"), so we search inside the text.
      const criteria = q.type === 'many' ? `*${choice}*` : choice;
      const r = rows.length + 1;
      rows.push([choice, `=COUNTIF(${ref}${col}2:${col}, "${criteria}")`, `=IF($B$1=0, 0, B${r}/$B$1)`]);
    });
    rows.push(['', '', '']);
  });

  summary.getRange(1, 1, rows.length, 3).setValues(rows);
  summary.getRange(1, 1, 1, 2).setFontWeight('bold').setBackground('#B6D7A8');
  summary.getRange(1, 3, rows.length, 1).setNumberFormat('0%');
  headerRows.forEach((r) => summary.getRange(r, 1, 1, 3).setFontWeight('bold').setBackground('#CFE2F3'));
  summary.setColumnWidth(1, 420);
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

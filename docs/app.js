/* EnvReplay Incident Room. All run outcomes come from checked-in evidence. */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const checks = ['ci', 'deployment', 'regression'];
  const state = { check: 'deployment', phase: 'before', file: 'app.py', report: null, diff: '' };

  function httpStatus(output) {
    const match = output.match(/GET\s+\S+\s+->\s+HTTP\s+(\d+)/);
    if (!match) throw new Error('A replay result is missing its HTTP status.');
    return match[1];
  }

  function validate(report, before, configs, diff) {
    if (!report || report.verdict !== 'PASS' || report.bob_status !== 'success' || report.bob_exit_code !== 0) {
      throw new Error('The preserved Bob run does not have a successful independent verdict.');
    }
    if (!report.bob_task_id || !diff.includes('diff --git a/app.py') || !diff.includes('diff --git a/replay.py')) {
      throw new Error('The Bob task or its two-file patch is missing.');
    }
    if (!Array.isArray(report.changed_files) ||
        !['app.py', 'replay.py'].every((file) => report.changed_files.includes(file))) {
      throw new Error('The run does not record both application files as changed.');
    }
    for (const name of checks) {
      const first = report.before?.[name];
      const last = report.after?.[name];
      if (!first || !last || !before[name] || first.output !== before[name].output || first.exit_code !== before[name].exit_code) {
        throw new Error(`Evidence for ${name} is missing or does not match its baseline file.`);
      }
    }
    if (configs.ci.public_base_path !== '' || configs.deployment.public_base_path !== '/service') {
      throw new Error('The published configuration differs from the documented incident.');
    }
    if (httpStatus(report.before.ci.output) !== '200' || httpStatus(report.before.deployment.output) !== '404' ||
        httpStatus(report.after.deployment.output) !== '200') {
      throw new Error('The preserved HTTP evidence does not match this incident.');
    }
    if (report.before.ci.exit_code !== 0 || report.before.deployment.exit_code !== 1 ||
        report.before.regression.exit_code !== 1 || checks.some((name) => report.after[name].exit_code !== 0)) {
      throw new Error('The independent before/after exit codes do not match this verified run.');
    }
  }

  async function load() {
    $('error').hidden = true;
    $('loaded').hidden = true;
    $('loading').hidden = false;
    $('incident-content').setAttribute('aria-busy', 'true');
    try {
      const paths = ['report.json', 'before.json', 'ci.json', 'deployment.json', 'bob.diff'];
      const responses = await Promise.all(paths.map((path) => fetch(`./data/${path}`)));
      for (let i = 0; i < responses.length; i++) {
        if (!responses[i].ok) throw new Error(`Could not load ${paths[i]} (HTTP ${responses[i].status}).`);
      }
      const [report, before, ci, deployment, diff] = await Promise.all([
        responses[0].json(), responses[1].json(), responses[2].json(), responses[3].json(), responses[4].text()
      ]);
      validate(report, before, { ci, deployment }, diff);
      state.report = report;
      state.diff = diff;
      renderProfiles(ci, deployment);
      renderReplay();
      renderBob();
      renderVerification();
      $('loading').hidden = true;
      $('loaded').hidden = false;
    } catch (error) {
      $('loading').hidden = true;
      $('error-detail').textContent = `${error.message} Serve the repository with a local web server or view the published Pages site.`;
      $('error').hidden = false;
    } finally {
      $('incident-content').setAttribute('aria-busy', 'false');
    }
  }

  function renderProfiles(ci, deployment) {
    $('ci-base').textContent = JSON.stringify(ci.public_base_path);
    $('deployment-base').textContent = JSON.stringify(deployment.public_base_path);
    $('ci-path').textContent = ci.public_base_path + '/api/health';
    $('deployment-path').textContent = deployment.public_base_path + '/api/health';
    $('ci-http').textContent = 'HTTP ' + httpStatus(state.report.before.ci.output);
    $('deployment-http').textContent = 'HTTP ' + httpStatus(state.report.before.deployment.output);
    $('hero-request').textContent = deployment.public_base_path + '/api/health';
    $('hero-ci-http').textContent = httpStatus(state.report.before.ci.output);
    $('hero-http').textContent = httpStatus(state.report.before.deployment.output);
    $('ribbon-symptom').textContent = 'HTTP ' + httpStatus(state.report.before.deployment.output);
    $('ribbon-task').textContent = state.report.bob_task_id.slice(0, 8) + '…';
    $('ribbon-checks').textContent = checks.filter((name) => state.report.after[name].exit_code === 0).length + ' / ' + checks.length;
    $('proof-ribbon').hidden = false;
  }

  function renderReplay() {
    const comparing = state.phase === 'compare';
    $('console-panel').hidden = comparing;
    $('compare-panel').hidden = !comparing;
    $('console-phase').textContent = comparing ? 'SAME COMMAND / TWO ENVIRONMENTS IN TIME' : state.phase === 'before' ? 'BEFORE REPAIR' : 'AFTER BOB REPAIR';
    $('console-exit').textContent = comparing ? 'BEFORE → AFTER' : `EXIT ${state.report[state.phase][state.check].exit_code}`;
    $('console-exit').className = comparing ? '' : state.report[state.phase][state.check].exit_code === 0 ? 'console-exit-pass' : 'console-exit-fail';
    if (comparing) {
      const panel = $('compare-panel');
      panel.replaceChildren();
      for (const [phase, label] of [['before', 'BEFORE REPAIR'], ['after', 'AFTER BOB']]) {
        const item = state.report[phase][state.check];
        const pane = document.createElement('div'); pane.className = 'compare-pane ' + (item.exit_code === 0 ? 'compare-pass' : 'compare-fail');
        const heading = document.createElement('div'); heading.className = 'compare-heading';
        const title = document.createElement('strong'); title.textContent = label;
        const exit = document.createElement('span'); exit.textContent = 'EXIT ' + item.exit_code;
        heading.append(title, exit);
        const command = document.createElement('div'); command.className = 'command-line'; command.textContent = '$ ' + item.command;
        const output = document.createElement('pre'); output.textContent = item.output;
        pane.append(heading, command, output); panel.append(pane);
      }
    } else {
      const item = state.report[state.phase][state.check];
      $('console-command').textContent = item.command;
      $('console-output').textContent = item.output;
    }
    $('console-source').href = state.phase === 'before' ? './data/before.json' : './data/report.json';
    for (const tab of document.querySelectorAll('[data-check]')) {
      const selected = tab.dataset.check === state.check;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    }
    $('console-panel').setAttribute('aria-labelledby', 'tab-' + state.check);
    $('compare-panel').setAttribute('aria-labelledby', 'tab-' + state.check);
    for (const phase of ['before', 'after', 'compare']) {
      $('phase-' + phase).classList.toggle('active', state.phase === phase);
      $('phase-' + phase).setAttribute('aria-pressed', String(state.phase === phase));
    }
  }

  function renderBob() {
    $('task-id').textContent = state.report.bob_task_id;
    $('task-verdict').textContent = state.report.verdict;
    renderDiff();
  }

  function renderDiff() {
    const marker = `diff --git a/${state.file} b/${state.file}`;
    const start = state.diff.indexOf(marker);
    if (start < 0) throw new Error(`The Bob patch has no ${state.file} section.`);
    const end = state.diff.indexOf('\ndiff --git ', start + marker.length);
    const section = state.diff.slice(start, end < 0 ? undefined : end + 1);
    const output = $('diff-output');
    output.replaceChildren();
    for (const line of section.trimEnd().split('\n')) {
      const span = document.createElement('span');
      span.className = 'diff-line';
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff --git') || line.startsWith('index ')) span.classList.add('header');
      else if (line.startsWith('+')) span.classList.add('add');
      else if (line.startsWith('-')) span.classList.add('del');
      else if (line.startsWith('@@')) span.classList.add('hunk');
      span.textContent = line;
      output.append(span);
    }
    for (const tab of document.querySelectorAll('[data-file]')) {
      const selected = tab.dataset.file === state.file;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    }
    output.setAttribute('aria-labelledby', state.file === 'app.py' ? 'diff-tab-app' : 'diff-tab-replay');
  }

  function renderVerification() {
    const tbody = $('result-rows');
    const details = $('verification-details');
    tbody.replaceChildren();
    details.replaceChildren();
    for (const name of checks) {
      const before = state.report.before[name];
      const after = state.report.after[name];
      const row = document.createElement('tr');
      const label = document.createElement('td'); label.textContent = name;
      const first = document.createElement('td'); first.className = 'exit ' + (before.exit_code ? 'fail' : 'pass'); first.textContent = before.exit_code;
      const last = document.createElement('td'); last.className = 'exit ' + (after.exit_code ? 'fail' : 'pass'); last.textContent = after.exit_code;
      const result = document.createElement('td'); result.className = 'result-pass'; result.textContent = after.exit_code === 0 ? 'PASS ✓' : 'FAIL';
      row.append(label, first, last, result);
      tbody.append(row);

      const section = document.createElement('section'); section.className = 'detail-check';
      const title = document.createElement('h3'); title.textContent = name;
      const pair = document.createElement('div'); pair.className = 'detail-pair';
      for (const [phase, item] of [['Before', before], ['After Bob', after]]) {
        const pane = document.createElement('div');
        const phaseLabel = document.createElement('span'); phaseLabel.className = 'detail-label'; phaseLabel.textContent = `${phase.toUpperCase()} / EXIT ${item.exit_code}`;
        const command = document.createElement('code'); command.textContent = '$ ' + item.command;
        const output = document.createElement('pre'); output.textContent = item.output;
        pane.append(phaseLabel, command, output); pair.append(pane);
      }
      section.append(title, pair); details.append(section);
    }
  }

  function setupTabs(selector, values, callback) {
    const tabs = Array.from(document.querySelectorAll(selector));
    for (const tab of tabs) {
      tab.addEventListener('click', () => callback(tab.dataset[values]));
      tab.addEventListener('keydown', (event) => {
        if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const index = tabs.indexOf(tab);
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        tabs[next].focus(); tabs[next].click();
      });
    }
  }

  setupTabs('[data-check]', 'check', (name) => { state.check = name; renderReplay(); });
  setupTabs('[data-file]', 'file', (name) => { state.file = name; renderDiff(); });
  $('phase-before').addEventListener('click', () => { state.phase = 'before'; renderReplay(); });
  $('phase-after').addEventListener('click', () => { state.phase = 'after'; renderReplay(); });
  $('phase-compare').addEventListener('click', () => { state.phase = 'compare'; renderReplay(); });
  $('retry').addEventListener('click', load);
  $('copy-command').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('reproduce-command').textContent);
      $('copy-command').textContent = 'Copied';
      setTimeout(() => { $('copy-command').textContent = 'Copy command'; }, 1700);
    } catch {
      $('copy-command').textContent = 'Select command above';
    }
  });
  load();
})();

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
  delete window.__AURA_RUNTIME_CONFIG__;
});

afterEach(() => {
  document.body.innerHTML = "";
  delete window.__AURA_RUNTIME_CONFIG__;
});

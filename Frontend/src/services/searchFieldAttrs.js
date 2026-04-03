export function createSearchFieldAttrs(name = 'search') {
    return {
        autocomplete: 'off',
        autocorrect: 'off',
        autocapitalize: 'none',
        spellcheck: 'false',
        inputmode: 'search',
        enterkeyhint: 'search',
        name,
        'data-form-type': 'other',
        'data-1p-ignore': 'true',
        'data-lpignore': 'true',
        'data-bwignore': 'true',
    }
}

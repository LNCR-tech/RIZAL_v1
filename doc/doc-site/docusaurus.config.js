// @ts-check
require('dotenv').config();

const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Aura Documentation',
  tagline: 'Attendance, events, and technical guides',
  favicon: 'img/favicon.ico',

  url: process.env.DOCUSAURUS_SITE_URL || 'https://docs.aura.local',
  baseUrl: '/',

  organizationName: 'aura',
  projectName: 'aura-docs',

  onBrokenLinks: 'warn',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          routeBasePath: '/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'Aura Docs',
        logo: {
          alt: 'Aura Logo',
          src: 'img/logo.png',
          srcDark: 'img/logo-white.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'userSidebar',
            position: 'left',
            label: 'Guides',
          },
          {
            to: '/updates/latest-implementation',
            position: 'left',
            label: 'Latest Changes',
          },
          {
            type: 'docSidebar',
            sidebarId: 'technicalSidebar',
            position: 'left',
            label: 'Technical Docs',
            className: 'dev-only',
          },
          {
            href: 'https://github.com/aura/aura',
            label: 'Repository',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'light',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting started',
                to: '/user/getting-started',
              },
              {
                label: 'Latest changes',
                to: '/updates/latest-implementation',
              },
              {
                label: 'FAQ',
                to: '/user/faq',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Support',
                href: '#',
              },
            ],
          },
        ],
        copyright: `Copyright (c) ${new Date().getFullYear()} Aura. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['python', 'bash', 'json'],
      },
    }),

  customFields: {
    authEnabled: process.env.DOCUSAURUS_AUTH_ENABLED !== 'false',
    defaultRole: process.env.DOCUSAURUS_DEFAULT_ROLE || 'student',
    authorizedEmails: process.env.DOCUSAURUS_AUTHORIZED_EMAILS || '',
    roles: {
      technical: ['admin', 'campus-admin', 'school-it'],
      eventManager: ['admin', 'campus-admin', 'ssg', 'sg', 'org'],
      user: ['admin', 'campus-admin', 'school-it', 'ssg', 'sg', 'org', 'student'],
    },
  },
};

module.exports = config;

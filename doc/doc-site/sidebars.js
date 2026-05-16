/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  userSidebar: [
    {
      type: 'category',
      label: 'Start here',
      items: ['index', 'user/getting-started', 'updates/latest-implementation'],
    },
    {
      type: 'category',
      label: 'User manual',
      items: [
        'user/user-manual/overview',
        'user/user-manual/attendance',
        'user/user-manual/events',
        'user/user-manual/notifications',
        'user/user-manual/profile',
      ],
    },
    {
      type: 'category',
      label: 'Mobile and support',
      items: ['user/mobile-guide', 'user/troubleshooting', 'user/faq'],
    },
  ],

  technicalSidebar: [
    {
      type: 'category',
      label: 'API reference',
      items: [
        'technical/api/overview',
        'technical/api/authentication',
        'technical/api/endpoints',
        'technical/api/websockets',
      ],
    },
    {
      type: 'category',
      label: 'Backend',
      items: [
        'technical/backend/architecture',
        'technical/backend/database',
        'technical/backend/services',
      ],
    },
    {
      type: 'category',
      label: 'Frontend',
      items: [
        'technical/frontend/architecture',
        'technical/frontend/components',
        'technical/frontend/state-management',
        'technical/frontend/docusaurus-rbac-architecture',
      ],
    },
    {
      type: 'category',
      label: 'AI assistant',
      items: ['technical/assistant/overview', 'technical/assistant/mcp-integration'],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: ['technical/deployment/docker', 'technical/deployment/production'],
    },
  ],
};

module.exports = sidebars;

export const CONSTANTS = {
  PAGINATION: {
    DEFAULT_PAGE: 1,
    DEFAULT_SIZE: 10,
  },
  STORAGE_KEYS: {
    AUTH_TOKEN: 'auth_token',
    USER_INFO: 'user_info',
  },
  USER_ROLES: {
    ADMIN: 'admin',
    BUSINESS_USER: 'business_user',
    EXECUTIVE: 'executive',
    VIEWER: 'viewer',
  },
  AUDIT_TYPES: [
    { label: 'Quick Scan', description: 'Automated scan for immediate feedback', value: 'quick' },
    { label: 'Deep Scan', description: 'Comprehensive accessibility audit', value: 'deep' },
    { label: 'Regression Scan', description: 'Compare against baseline', value: 'regression' }
  ],
  SCAN_CONFIG: {
    QUICK: { max_urls: 25, scan_type: 'quick', ai_analysis: true },
    DEEP: { max_urls: 500, scan_type: 'deep', ai_analysis: true },
    REGRESSION: { max_urls: 100, scan_type: 'regression', ai_analysis: false }
  }
};

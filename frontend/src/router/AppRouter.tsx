import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  redirect
} from '@tanstack/react-router';

import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import Dashboard from '../pages/dashboard/Dashboard';
import ProtectedRoute from './ProtectedRoute';
import { SuccessPage, MaintenancePage, NotFoundPage } from '../pages/common';
import AgentsConsole from '../pages/agents/AgentsConsole';
import AuditsPage from '../pages/audits/AuditsPage';
import AuditDetailsPage from '../pages/audits/AuditDetailsPage';
import ApiKeysPage from '../pages/api-keys/ApiKeysPage';
import BillingPage from '../pages/billing/BillingPage';
import CreditsPage from '../pages/credits/CreditsPage';
import UserManagementPage from '../pages/users/UserManagementPage';
import CredentialsPage from '../pages/credentials/CredentialsPage';
import ProjectsPage from '../pages/projects/ProjectsPage';

// Create a root route with a custom 404 fallback component
const rootRoute = createRootRoute({
  component: () => (
    <>
      <Outlet />
    </>
  ),
  notFoundComponent: NotFoundPage,
});

// Layout route for authenticated routes using the ProtectedRoute component
const protectedLayout = createRoute({
  id: '_protected',
  getParentRoute: () => rootRoute,
  component: ProtectedRoute,
});

// Layout route for public routes (e.g. login, register) with an unauthenticated guard
const publicLayout = createRoute({
  id: '_public',
  getParentRoute: () => rootRoute,
  beforeLoad: () => {
    const token = localStorage.getItem('auth_token');
    const orgId = localStorage.getItem('org_id') || 'default';
    if (token) {
      throw redirect({
        to: '/org/$orgId/dashboard',
        params: { orgId }
      });
    }
  },
});

// Create concrete routes
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: () => {
    const token = localStorage.getItem('auth_token');
    const orgId = localStorage.getItem('org_id');
    if (token && orgId) {
      throw redirect({
        to: '/org/$orgId/dashboard',
        params: { orgId }
      });
    } else {
      throw redirect({
        to: '/auth/signin'
      });
    }
  },
});

const successRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/success',
  component: SuccessPage,
});

const maintenanceRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/maintenance',
  component: MaintenancePage,
});

const loginRoute = createRoute({
  getParentRoute: () => publicLayout,
  path: '/auth/signin',
  component: Login,
});

const registerRoute = createRoute({
  getParentRoute: () => publicLayout,
  path: '/auth/signup',
  component: Register,
});

// Tenant Layout with Org Param validation
const tenantLayout = createRoute({
  getParentRoute: () => protectedLayout,
  path: '/org/$orgId',
  beforeLoad: ({ params }) => {
    const userOrgId = localStorage.getItem('org_id');
    if (userOrgId && params.orgId !== userOrgId) {
      throw redirect({
        to: '/org/$orgId/dashboard',
        params: { orgId: userOrgId }
      });
    }
  },
});

const dashboardRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/dashboard',
  component: Dashboard,
});



const agentsRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/agents',
  component: AgentsConsole,
});

const auditsRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/audits',
  component: AuditsPage,
});

const auditDetailsRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/audits/$taskId',
  component: AuditDetailsPage,
});

const billingRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/billing',
  component: BillingPage,
});

const creditsRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/credits',
  component: CreditsPage,
});

const apiKeysRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/api-keys',
  component: ApiKeysPage,
});

const usersRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/users',
  component: UserManagementPage,
});

const credentialsRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/credentials',
  component: CredentialsPage,
});

const projectsRoute = createRoute({
  getParentRoute: () => tenantLayout,
  path: '/projects',
  component: ProjectsPage,
});

// Splat catch-all route for any other unmatched URL paths
const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '$',
  component: NotFoundPage,
});

// Create the route tree with layout hierarchies
const routeTree = rootRoute.addChildren([
  indexRoute,
  successRoute,
  maintenanceRoute,
  publicLayout.addChildren([loginRoute, registerRoute]),
  protectedLayout.addChildren([
    tenantLayout.addChildren([dashboardRoute, agentsRoute, auditsRoute, auditDetailsRoute, billingRoute, creditsRoute, apiKeysRoute, usersRoute, credentialsRoute, projectsRoute])
  ]),
  notFoundRoute
]);

// Create the router
export const router = createRouter({ routeTree });

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

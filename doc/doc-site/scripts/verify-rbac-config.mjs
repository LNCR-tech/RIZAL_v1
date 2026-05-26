import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const config = require("../docusaurus.config.js");

const fields = config.customFields || {};
const roles = fields.roles || {};

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

// This script is a lightweight runnable test for the docs auth/RBAC contract.
assert(fields.authEnabled === true || fields.authEnabled === false, "authEnabled must be boolean-like.");
assert(typeof fields.defaultRole === "string" && fields.defaultRole.length > 0, "defaultRole is required.");
assert(Array.isArray(roles.technical), "technical roles must be configured.");
assert(Array.isArray(roles.user), "user roles must be configured.");
assert(roles.technical.includes("admin"), "admin must access technical docs.");
assert(roles.technical.includes("campus-admin"), "campus-admin must access technical docs.");
assert(roles.technical.includes("school-it"), "school-it must access technical docs.");
assert(roles.user.includes("student"), "student must access user docs.");
assert(config.presets?.length > 0, "Docusaurus presets must be configured.");

console.log("Docs RBAC config check passed.");

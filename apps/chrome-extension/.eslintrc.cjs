module.exports = {
  root: true,
  env: { browser: true, es2022: true, webextensions: true },
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  plugins: ["@typescript-eslint", "react-hooks"],
  rules: {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",
    "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    // Enterprise naming convention (industry standard): camelCase for values/functions,
    // PascalCase for types/classes/React components/enums, UPPER_CASE or camelCase for
    // constants. `leadingUnderscore`/`trailingUnderscore` "allow" covers private-field
    // and unused-arg conventions used elsewhere in this codebase.
    "@typescript-eslint/naming-convention": [
      "error",
      { selector: "default", format: ["camelCase"], leadingUnderscore: "allow", trailingUnderscore: "allow" },
      { selector: "import", format: null },
      { selector: "variable", format: ["camelCase", "UPPER_CASE", "PascalCase"], leadingUnderscore: "allow" },
      { selector: "parameter", format: ["camelCase"], leadingUnderscore: "allow" },
      { selector: "property", format: null },
      { selector: "typeLike", format: ["PascalCase"] },
      { selector: "enumMember", format: ["PascalCase", "UPPER_CASE"] },
      { selector: "function", format: ["camelCase", "PascalCase"] },
    ],
  },
  ignorePatterns: ["dist", "node_modules"],
};

import type { Config } from "jest";

const config: Config = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: "tsconfig.jest.json",
        jsx: "react-jsx",
      },
    ],
    "^.+\\.js$": [
      "ts-jest",
      {
        tsconfig: "tsconfig.jest.json",
        jsx: "react-jsx",
      },
    ],
  },
  moduleNameMapper: {
    "\\.(css|less|scss)$": "<rootDir>/__mocks__/styleMock.js",
    "^@/(.*)$": "<rootDir>/$1",
  },
  transformIgnorePatterns: [],
};

export default config;

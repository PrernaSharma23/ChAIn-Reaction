import _ from "lodash";

export const getRepoMap = () => JSON.parse(sessionStorage.getItem("repoMap") || "{}");

/** Get repo name from ID */
export const getRepoName = (id: string): string =>
  _.get(getRepoMap(), id, id);

/** Get repo ID from name */
export const getRepoId = (name: string): string | undefined =>
  _.invert(getRepoMap())[name];

/** Get all repo IDs as string[] */
export const getAllRepoIds = (): string[] =>
  _.keys(getRepoMap());
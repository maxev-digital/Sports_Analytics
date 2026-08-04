/**
 * Structured logger — pino-compatible interface for the frontend.
 * In production builds, info and debug are suppressed.
 * Errors and warnings are always emitted.
 */

type LogArg = unknown;

const isProd = import.meta.env.PROD;

function formatMsg(level: string, msg: string, ...args: LogArg[]): void {
  if (isProd && (level === 'info' || level === 'debug')) return;
  const method = level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log';
  // eslint-disable-next-line no-console
  (console[method] as (...a: LogArg[]) => void)(msg, ...args);
}

export const logger = {
  debug: (msg: string, ...args: LogArg[]) => formatMsg('debug', msg, ...args),
  info:  (msg: string, ...args: LogArg[]) => formatMsg('info',  msg, ...args),
  warn:  (msg: string, ...args: LogArg[]) => formatMsg('warn',  msg, ...args),
  error: (msg: string, ...args: LogArg[]) => formatMsg('error', msg, ...args),
};

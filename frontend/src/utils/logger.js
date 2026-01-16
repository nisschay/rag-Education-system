// Simple logging utility for frontend
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

const currentLevel = import.meta.env.DEV ? LOG_LEVELS.DEBUG : LOG_LEVELS.INFO;

const formatMessage = (level, module, message, data) => {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level}] [${module}] ${message}`;
};

const createLogger = (module) => {
  return {
    debug: (message, data = null) => {
      if (currentLevel <= LOG_LEVELS.DEBUG) {
        console.log(formatMessage('DEBUG', module, message), data || '');
      }
    },
    info: (message, data = null) => {
      if (currentLevel <= LOG_LEVELS.INFO) {
        console.info(formatMessage('INFO', module, message), data || '');
      }
    },
    warn: (message, data = null) => {
      if (currentLevel <= LOG_LEVELS.WARN) {
        console.warn(formatMessage('WARN', module, message), data || '');
      }
    },
    error: (message, data = null) => {
      if (currentLevel <= LOG_LEVELS.ERROR) {
        console.error(formatMessage('ERROR', module, message), data || '');
      }
    },
  };
};

export default createLogger;

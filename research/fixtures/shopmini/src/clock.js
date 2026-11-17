// Injectable clock so tests can control time.
let nowFn = () => new Date();
module.exports = { now: () => nowFn(), _setNow: (fn) => { nowFn = fn; } };

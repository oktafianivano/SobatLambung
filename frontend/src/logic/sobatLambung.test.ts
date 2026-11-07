import test from 'node:test';
import assert from 'node:assert/strict';
import {
  normalizeWhatsAppNumber,
  validatePassword,
  generateWhatsAppReminderMessage,
  getNextStaticAlarm,
  STATIC_SCHEDULES
} from './sobatLambung';

test('normalizeWhatsAppNumber correctly formats Indonesian numbers', () => {
  // Test leading 0
  const r1 = normalizeWhatsAppNumber('081234567890');
  assert.equal(r1.isValid, true);
  assert.equal(r1.formatted, '6281234567890');

  // Test already 62
  const r2 = normalizeWhatsAppNumber('6281234567890');
  assert.equal(r2.isValid, true);
  assert.equal(r2.formatted, '6281234567890');

  // Test with spaces and dashes
  const r3 = normalizeWhatsAppNumber('+62 812-3456-7890');
  assert.equal(r3.isValid, true);
  assert.equal(r3.formatted, '6281234567890');

  // Test invalid short number
  const r4 = normalizeWhatsAppNumber('08123');
  assert.equal(r4.isValid, false);
  assert.ok(r4.error);
});

test('validatePassword checks minimum length', () => {
  const short = validatePassword('12345');
  assert.equal(short.isValid, false);
  assert.ok(short.error?.includes('minimal 6 karakter'));

  const valid = validatePassword('rahasia123');
  assert.equal(valid.isValid, true);
});

test('generateWhatsAppReminderMessage contains name and menu recommendations', () => {
  const msg = generateWhatsAppReminderMessage('Dimas Arya', 'breakfast');
  assert.ok(msg.includes('Dimas Arya'));
  assert.ok(msg.includes('Sarapan Pagi Ramah Lambung'));
  assert.ok(msg.includes('Bubur ayam'));
  assert.ok(msg.includes('07:00 WIB'));
});

test('getNextStaticAlarm returns appropriate upcoming time', () => {
  // At 06:30, next is breakfast (07:00)
  const alarm1 = getNextStaticAlarm(6, 30);
  assert.equal(alarm1.id, 'breakfast');

  // At 09:00, next is lunch (12:00)
  const alarm2 = getNextStaticAlarm(9, 0);
  assert.equal(alarm2.id, 'lunch');

  // At 15:00, next is dinner (18:30)
  const alarm3 = getNextStaticAlarm(15, 0);
  assert.equal(alarm3.id, 'dinner');

  // At 21:00, wraps to breakfast tomorrow
  const alarm4 = getNextStaticAlarm(21, 0);
  assert.equal(alarm4.id, 'breakfast');
});

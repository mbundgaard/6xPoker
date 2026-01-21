// Player store - manages nickname in localStorage

const STORAGE_KEY = '6xpoker_nickname';

function createPlayerStore() {
  let nickname = $state<string | null>(null);

  // Load from localStorage on init
  if (typeof window !== 'undefined') {
    nickname = localStorage.getItem(STORAGE_KEY);
  }

  return {
    get nickname() {
      return nickname;
    },
    set nickname(value: string | null) {
      nickname = value;
      if (typeof window !== 'undefined') {
        if (value) {
          localStorage.setItem(STORAGE_KEY, value);
        } else {
          localStorage.removeItem(STORAGE_KEY);
        }
      }
    },
    get hasNickname() {
      return !!nickname;
    },
    clear() {
      this.nickname = null;
    }
  };
}

export const player = createPlayerStore();

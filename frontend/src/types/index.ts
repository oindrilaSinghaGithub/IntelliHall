export interface NavLink {
  label: string;
  href: string;
}

export interface Feature {
  title: string;
  description: string;
}

export interface AppState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
}

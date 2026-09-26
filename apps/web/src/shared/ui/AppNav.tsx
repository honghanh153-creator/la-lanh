import { BookmarkSimple, HeartStraight, House, Planet, UserCircle } from "@phosphor-icons/react";
import { NavLink } from "react-router-dom";

const items = [
  { to: "/home", label: "Hôm nay", icon: House },
  { to: "/insights", label: "Bản đồ", icon: Planet },
  { to: "/radar", label: "Hợp gu", icon: HeartStraight },
  { to: "/saved", label: "Đã lưu", icon: BookmarkSimple },
  { to: "/profile", label: "Mình", icon: UserCircle },
] as const;

export function AppNav() {
  return (
    <nav aria-label="Điều hướng chính" className="app-nav">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink className={({ isActive }) => isActive ? "app-nav__item app-nav__item--active" : "app-nav__item"} key={to} to={to}>
          <Icon aria-hidden="true" size={24} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

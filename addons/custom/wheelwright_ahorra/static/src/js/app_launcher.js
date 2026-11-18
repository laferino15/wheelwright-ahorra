/** @odoo-module **/
import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useBus, useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { NavBar } from "@web/webclient/navbar/navbar";
import { WebClient } from "@web/webclient/webclient";

const LAUNCHER = "wheelwright_ahorra.app_launcher";
const normalize = (value) => (value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase().trim();

export class WheelAppLauncher extends Component {
    static template = "wheelwright_ahorra.AppLauncher";
    static props = { ...standardActionServiceProps };

    setup() {
        this.menu = useService("menu");
        this.state = useState({ query: "", busy: false, revision: 0 });
        this.search = useRef("search");
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.state.revision++);
        onMounted(() => this.search.el?.focus());
    }

    firstAction(menu) {
        if (menu.actionID) return menu;
        for (const id of menu.children || []) {
            const target = this.firstAction(this.menu.getMenu(id));
            if (target) return target;
        }
        return null;
    }

    get entries() {
        // Menus come from Odoo's permission-filtered menu service, never sudo/RPC.
        void this.state.revision;
        const apps = this.menu.getApps();
        const query = normalize(this.state.query);
        const appMap = new Map(apps.map((app) => [app.id, app]));
        const source = query ? this.menu.getAll().filter((item) => item.id !== "root" && item.actionID) : apps;
        return source.filter((item) => {
            const app = appMap.get(item.appID) || item;
            return !query || normalize(`${item.name} ${app.name}`).includes(query);
        }).map((item) => {
            const app = appMap.get(item.appID) || item;
            const target = this.firstAction(item);
            return { id: item.id, name: item.name, subtitle: query && item.id !== app.id ? app.name : "",
                app, target, href: target ? `/odoo/${target.actionPath || "action-" + target.actionID}` : "#" };
        }).filter((entry) => entry.target);
    }

    get currentAppId() { return this.menu.getCurrentApp()?.id; }

    icon(entry) {
        if (entry.app.xmlid === "wheelwright_ahorra.marketplace_menu") return "/wheelwright_ahorra/static/src/img/app-icon.svg";
        if (entry.app.webIconData) return entry.app.webIconData;
        return "/web/static/img/default_icon_app.png";
    }

    fontIcon(entry) {
        const parts = (entry.app.webIcon || "").split(",");
        return !entry.app.webIconData && parts.length === 3 ? parts[0] : "";
    }

    iconStyle(entry) {
        const [, color, background] = (entry.app.webIcon || "").split(",");
        return `color:${color || "#07533f"};background-color:${background || "#edf3e8"}`;
    }

    async open(entry, ev) {
        // Preserve Ctrl/Cmd/middle-click links and Odoo's unsaved-record guard.
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button === 1) return;
        ev.preventDefault();
        if (this.state.busy) return;
        this.state.busy = true;
        try { await this.menu.selectMenu(entry.target); }
        finally { this.state.busy = false; }
    }

    onSearchKey(ev) {
        if (ev.key === "Escape") this.state.query = "";
        if (ev.key === "Enter" && this.entries.length) this.open(this.entries[0], ev);
    }
}

registry.category("actions").add(LAUNCHER, WheelAppLauncher);

patch(WebClient.prototype, {
    _loadDefaultApp() {
        if (this.env.services.pwa?.isScopedApp) return super._loadDefaultApp(...arguments);
        return this.actionService.doAction(LAUNCHER, { clearBreadcrumbs: true });
    },
});

patch(NavBar.prototype, {
    openWheelApps() {
        return this.actionService.doAction(LAUNCHER, { clearBreadcrumbs: true });
    },
});

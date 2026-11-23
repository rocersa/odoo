/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {Component, onMounted, useState} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {
    BarcodeVideoScanner,
    isBarcodeScannerSupported,
} from "@web/core/barcode/barcode_video_scanner";
import {registry} from "@web/core/registry";
import {standardActionServiceProps} from "@web/webclient/actions/action_service";
import {useBus, useService} from "@web/core/utils/hooks";

const MODEL = "stock.yard.relocate";

export class YardRelocate extends Component {
    static template = "stock_barcode_yard_relocate.YardRelocate";
    static components = {BarcodeVideoScanner};
    static props = {...standardActionServiceProps};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.barcodeService = useService("barcode");
        this.state = useState({
            stage: "source",
            source: null,
            destination: null,
            lines: [],
            busy: false,
            cameraScannerSupported: isBarcodeScannerSupported(),
            cameraScannedEnabled: false,
        });
        // Serialise scans and the confirm, so a quick second scan is not lost.
        this._queue = Promise.resolve();
        // A label left in front of the camera is detected again after the pause;
        // ignore a repeat of the same barcode for a moment instead of warning.
        this._lastScanned = {barcode: null, at: 0};
        useBus(this.barcodeService.bus, "barcode_scanned", (ev) =>
            this._enqueue(() => this.onBarcodeScanned(ev.detail.barcode))
        );
        // The same inline scanner the barcode app's count screen uses: it stays
        // mounted and armed across every step, and has no text input to raise the
        // on-screen keyboard.
        this.barcodeVideoScannerProps = {
            delayBetweenScan: 2000,
            facingMode: "environment",
            cssClass: "o_yard_relocate_video",
            onResult: (barcode) =>
                this._enqueue(() => this.onBarcodeScanned(barcode)),
            onError: (error) => this._onScannerError(error),
        };
        onMounted(() => this.startScanner());
    }

    get stepLabel() {
        const labels = {
            source: _t("1 of 3 · Source"),
            destination: _t("2 of 3 · Destination"),
            products: _t("3 of 3 · Products"),
        };
        return labels[this.state.stage];
    }

    get prompt() {
        const prompts = {
            source: _t("Scan the source location"),
            destination: _t("Scan the destination location"),
            products: _t("Scan each product that is there"),
        };
        return prompts[this.state.stage];
    }

    get promptHelp() {
        const help = {
            source: _t("The exact location the stock is leaving."),
            destination: _t("Where the stock is going. It must differ from the source."),
            products: _t("Each scan queues that product's full quantity here."),
        };
        return help[this.state.stage];
    }

    _enqueue(task) {
        this._queue = this._queue.then(task).catch((error) => this._notifyError(error));
    }

    startScanner() {
        if (this.state.cameraScannerSupported) {
            this.state.cameraScannedEnabled = true;
        }
    }

    _onScannerError(error) {
        this.state.cameraScannedEnabled = false;
        const message = error?.message || _t("Could not start the camera.");
        this.notification.add(message, {type: "warning"});
    }

    async onBarcodeScanned(barcode) {
        if (!barcode) {
            return;
        }
        const now = Date.now();
        if (
            barcode === this._lastScanned.barcode &&
            now - this._lastScanned.at < 3000
        ) {
            return;
        }
        this._lastScanned = {barcode, at: now};
        if ("vibrate" in window.navigator) {
            window.navigator.vibrate(100);
        }
        if (this.state.stage === "source") {
            await this._scanSource(barcode);
        } else if (this.state.stage === "destination") {
            await this._scanDestination(barcode);
        } else {
            await this._scanProduct(barcode);
        }
    }

    async _scanSource(barcode) {
        const result = await this.orm.call(MODEL, "resolve_location", [barcode]);
        if (!result.ok) {
            this.notification.add(result.warning, {type: "warning"});
            return;
        }
        this.state.source = {id: result.id, name: result.name};
        this.state.stage = "destination";
        this.notification.add(_t("Source: %s", result.name), {type: "success"});
    }

    async _scanDestination(barcode) {
        const result = await this.orm.call(MODEL, "resolve_location", [barcode]);
        if (!result.ok) {
            this.notification.add(result.warning, {type: "warning"});
            return;
        }
        if (this.state.source && result.id === this.state.source.id) {
            this.notification.add(
                _t("The destination must differ from the source."),
                {type: "danger"}
            );
            return;
        }
        this.state.destination = {id: result.id, name: result.name};
        this.state.stage = "products";
        this.notification.add(_t("Destination: %s", result.name), {type: "success"});
    }

    async _scanProduct(barcode) {
        if (!this.state.source) {
            return;
        }
        const result = await this.orm.call(MODEL, "scan_product", [
            this.state.source.id,
            barcode,
        ]);
        if (!result.ok) {
            this.notification.add(result.warning, {type: "warning"});
            return;
        }
        if (this.state.lines.some((line) => line.product_id === result.product_id)) {
            this.notification.add(
                _t("%s is already in the list.", result.name),
                {type: "info"}
            );
            return;
        }
        this.state.lines.push({
            product_id: result.product_id,
            name: result.name,
            qty: result.qty,
            uom: result.uom,
        });
        this.notification.add(
            _t("Queued %(name)s: %(qty)s %(uom)s", {
                name: result.name,
                qty: result.qty,
                uom: result.uom,
            }),
            {type: "success"}
        );
    }

    removeLine(productId) {
        this.state.lines = this.state.lines.filter(
            (line) => line.product_id !== productId
        );
    }

    onConfirm() {
        if (!this.state.lines.length || this.state.busy) {
            return;
        }
        this.state.busy = true;
        this._enqueue(() => this._confirm());
    }

    async _confirm() {
        try {
            if (!this.state.source || !this.state.destination || !this.state.lines.length) {
                return;
            }
            const productIds = this.state.lines.map((line) => line.product_id);
            const result = await this.orm.call(MODEL, "commit", [
                this.state.source.id,
                this.state.destination.id,
                productIds,
            ]);
            const moved = result.moved.length;
            const skipped = result.skipped.length;
            let message;
            if (moved === 1) {
                message = _t("Moved 1 product.");
            } else {
                message = _t("Moved %s products.", moved);
            }
            if (skipped) {
                message = _t("%(message)s Skipped: %(skipped)s", {
                    message,
                    skipped: result.skipped.join(", "),
                });
            }
            this.notification.add(message, {
                type: skipped ? "warning" : "success",
            });
            this.state.lines = [];
        } finally {
            this.state.busy = false;
        }
    }

    onStartOver() {
        if (!this.state.lines.length) {
            this._reset();
            return;
        }
        this.dialog.add(ConfirmationDialog, {
            title: _t("Start over?"),
            body: _t(
                "The queued products will be forgotten. Nothing has been moved yet."
            ),
            confirmLabel: _t("Start over"),
            cancelLabel: _t("Keep scanning"),
            confirm: () => this._reset(),
            cancel: () => {},
        });
    }

    _reset() {
        this.state.stage = "source";
        this.state.source = null;
        this.state.destination = null;
        this.state.lines = [];
        this.state.busy = false;
    }

    onClose() {
        if (this.env.config.breadcrumbs?.length > 1) {
            this.env.config.historyBack();
        } else {
            this.action.doAction("stock_barcode.stock_barcode_action_main_menu");
        }
    }

    _notifyError(error) {
        const message =
            error?.data?.message || error?.message || _t("Something went wrong.");
        this.notification.add(message, {type: "danger"});
    }
}

registry.category("actions").add("stock_barcode_yard_relocate", YardRelocate);

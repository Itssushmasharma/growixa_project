// Thin, typed wrapper around Razorpay's Checkout.js widget (GRX-BILL-007) -- loaded
// lazily from Razorpay's own CDN on first use, not bundled, matching how this codebase
// treats every other third-party script/API as a thin adapter rather than an SDK
// dependency.

export interface RazorpayCheckoutSuccessResponse {
  razorpay_payment_id: string;
  razorpay_order_id?: string;
  razorpay_subscription_id?: string;
  razorpay_signature?: string;
}

export interface RazorpayCheckoutOptions {
  key: string;
  name: string;
  description?: string;
  order_id?: string;
  subscription_id?: string;
  amount?: number;
  currency?: string;
  prefill?: { email?: string; name?: string };
  theme?: { color?: string };
  handler: (response: RazorpayCheckoutSuccessResponse) => void;
  modal?: { ondismiss?: () => void };
}

interface RazorpayCheckoutInstance {
  open: () => void;
}

interface RazorpayConstructor {
  new (options: RazorpayCheckoutOptions): RazorpayCheckoutInstance;
}

declare global {
  interface Window {
    Razorpay?: RazorpayConstructor;
  }
}

const CHECKOUT_SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js";

let scriptLoadPromise: Promise<void> | null = null;

function loadRazorpayScript(): Promise<void> {
  if (typeof window !== "undefined" && window.Razorpay) {
    return Promise.resolve();
  }
  if (!scriptLoadPromise) {
    scriptLoadPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = CHECKOUT_SCRIPT_URL;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => {
        scriptLoadPromise = null;
        reject(new Error("Failed to load Razorpay Checkout"));
      };
      document.body.appendChild(script);
    });
  }
  return scriptLoadPromise;
}

export async function openRazorpayCheckout(options: RazorpayCheckoutOptions): Promise<void> {
  await loadRazorpayScript();
  if (!window.Razorpay) {
    throw new Error("Razorpay Checkout failed to load");
  }
  new window.Razorpay(options).open();
}

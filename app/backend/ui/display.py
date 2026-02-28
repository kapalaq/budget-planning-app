"""Display - the frontend layer of the budget planner.

Collects user input (via InputHandler), sends dict requests to the
RequestHandler middleground, receives dict responses, and renders output.
"""

from typing import TYPE_CHECKING

from ui.input_handler import InputHandler

if TYPE_CHECKING:
    from api.request_handler import RequestHandler


class Display:
    """Frontend controller: input collection, request dispatch, rendering."""

    SEPARATOR = "=" * 50

    def __init__(self, handler: "RequestHandler"):
        self._handler = handler

    #  Main loop
    def run(self):
        """Main application loop."""
        self._show_welcome()

        running = True
        while running:
            try:
                running = self._tick()
            except KeyboardInterrupt:
                print()
                self._show_info("Use 'quit' to exit")
            except EOFError:
                running = False
                self._show_info("Goodbye!")

    def _tick(self) -> bool:
        """One iteration: process recurring, get command, dispatch."""
        # Materialise any due recurring transactions
        resp = self._handler.handle({"action": "process_recurring", "data": {}})
        count = resp.get("data", {}).get("generated_count", 0)
        if count > 0:
            self._show_info(f"{count} recurring transaction(s) generated")

        command_str = InputHandler.get_command()
        return self._route_command(command_str)

    #  Command routing
    def _route_command(self, command_str: str) -> bool:
        """Parse a command string and dispatch to the appropriate handler."""
        cmd = command_str.strip()
        cmd_lower = cmd.lower()

        # Simple commands
        if cmd_lower == "+":
            self._handle_add_transaction("income")
        elif cmd_lower == "-":
            self._handle_add_transaction("expense")
        elif cmd_lower == "+r":
            self._handle_add_recurring("income")
        elif cmd_lower == "-r":
            self._handle_add_recurring("expense")
        elif cmd_lower == "recurring":
            self._handle_recurring_list()
        elif cmd_lower == "transfer":
            self._handle_transfer()
        elif cmd_lower == "sort":
            self._handle_sort()
        elif cmd_lower == "filter":
            self._handle_filter()
        elif cmd_lower == "percent":
            self._handle_percentages()
        elif cmd_lower == "help":
            self._handle_help()
        elif cmd_lower in ("quit", "exit", "q"):
            self._show_info("Thank you for using Budget Planner. Goodbye!")
            return False
        elif cmd_lower in ("", "refresh", "home"):
            self._handle_dashboard()
        elif cmd_lower == "wallets":
            self._handle_wallets()
        elif cmd_lower == "add_wallet":
            self._handle_add_wallet()
        elif cmd_lower == "sort_wallets":
            self._handle_wallet_sorting()
        else:
            # Indexed commands  (show 1, edit 2, delete 3, show_rec 1, …)
            action, index = InputHandler.parse_indexed_command(cmd_lower)
            if action and index:
                if action == "show":
                    self._handle_show_transaction(index)
                elif action == "edit":
                    self._handle_edit_transaction(index)
                elif action == "delete":
                    self._handle_delete_transaction(index)
                elif action == "show_rec":
                    self._handle_show_recurring(index)
                elif action == "edit_rec":
                    self._handle_edit_recurring(index)
                elif action == "delete_rec":
                    self._handle_delete_recurring(index)
                else:
                    self._handle_named_or_unknown(cmd)
            else:
                self._handle_named_or_unknown(cmd)

        return True

    def _handle_named_or_unknown(self, cmd: str):
        """Try wallet-named commands, fall back to unknown."""
        action, name = InputHandler.parse_named_command(cmd)
        if action and name:
            act = action.lower()
            if act == "wallet":
                self._handle_wallet_detail(name)
                return
            elif act == "edit_wallet":
                self._handle_edit_wallet(name)
                return
            elif act == "delete_wallet":
                self._handle_delete_wallet(name)
                return
            elif act == "switch":
                self._handle_switch_wallet(name)
                return

        self._show_error(
            f"Unknown command: '{cmd}'. Type 'help' for available commands."
        )

    #  Welcome / dashboard
    def _show_welcome(self):
        print(f"\n{self.SEPARATOR}")
        print("   Welcome to Budget Planner!")
        print(self.SEPARATOR)
        self._handle_help()
        self._handle_dashboard()

    def _handle_dashboard(self):
        resp = self._handler.handle({"action": "get_dashboard", "data": {}})
        if resp["status"] == "error":
            self._show_info(resp["message"])
            return
        self._render_dashboard(resp["data"])

    def _handle_help(self):
        resp = self._handler.handle({"action": "get_help", "data": {}})
        cmds = resp["data"]["commands"]
        print("\n[*] Available Commands:")
        # Group headers
        groups = {
            "Transaction": [
                "+",
                "-",
                "transfer",
                "show <N>",
                "edit <N>",
                "delete <N>",
                "sort",
                "filter",
                "percent",
            ],
            "Wallet": [
                "wallets",
                "add_wallet",
                "wallet <name>",
                "edit_wallet <name>",
                "delete_wallet <name>",
                "switch <name>",
                "sort_wallets",
            ],
            "Recurring": [
                "+r",
                "-r",
                "recurring",
                "show_rec <N>",
                "edit_rec <N>",
                "delete_rec <N>",
            ],
            "General": ["home", "help", "quit"],
        }
        cmd_map = {c["command"]: c["description"] for c in cmds}
        for group, keys in groups.items():
            print(f"+--------- {group} Commands ---------+")
            for k in keys:
                desc = cmd_map.get(k, "")
                print(f"   {k:<20s} - {desc}")

    #  Transaction handlers
    def _handle_add_transaction(self, tt_name: str):
        tt_label = "Income" if tt_name == "income" else "Expense"
        resp = self._handler.handle(
            {"action": "get_categories", "data": {"transaction_type": tt_name}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return
        categories = resp["data"]["categories"]

        form = InputHandler.get_transaction_input(tt_label, categories)
        if form is None:
            self._show_error("Transaction cancelled")
            return

        form["transaction_type"] = tt_name
        resp = self._handler.handle({"action": "add_transaction", "data": form})
        self._render_message(resp)

    def _handle_show_transaction(self, index: int):
        resp = self._handler.handle(
            {"action": "get_transaction", "data": {"index": index}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return
        self._render_transaction_detail(resp["data"])

    def _handle_edit_transaction(self, index: int):
        resp = self._handler.handle(
            {"action": "get_transaction", "data": {"index": index}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return
        current = resp["data"]

        if current["is_transfer"]:
            edit_data = InputHandler.get_transfer_edit_input(current)
        else:
            cat_resp = self._handler.handle(
                {
                    "action": "get_categories",
                    "data": {"transaction_type": current["transaction_type"]},
                }
            )
            categories = cat_resp["data"]["categories"]
            edit_data = InputHandler.get_edit_input(current, categories)

        if edit_data is None:
            self._show_info("Edit cancelled")
            return

        edit_data["index"] = index
        resp = self._handler.handle({"action": "edit_transaction", "data": edit_data})
        self._render_message(resp)

    def _handle_delete_transaction(self, index: int):
        resp = self._handler.handle(
            {"action": "get_transaction", "data": {"index": index}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        self._render_transaction_detail(resp["data"])
        if resp["data"]["is_transfer"]:
            self._show_info(
                "This is a transfer. Deleting it will also remove "
                "the corresponding transaction from the other wallet."
            )

        if not InputHandler.confirm(
            "Are you sure you want to delete this transaction?"
        ):
            self._show_info("Deletion cancelled")
            return

        resp = self._handler.handle(
            {"action": "delete_transaction", "data": {"index": index}}
        )
        self._render_message(resp)

    # ================================================================== #
    #  Transfer handler                                                   #
    # ================================================================== #

    def _handle_transfer(self):
        resp = self._handler.handle({"action": "get_transfer_context", "data": {}})
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        from_wallet = resp["data"]["from_wallet"]
        targets = resp["data"]["target_wallets"]

        form = InputHandler.get_transfer_input(from_wallet, targets)
        if form is None:
            self._show_info("Transfer cancelled")
            return

        resp = self._handler.handle({"action": "transfer", "data": form})
        self._render_message(resp)

    #  Sorting handlers
    def _handle_sort(self):
        resp = self._handler.handle({"action": "get_sorting_options", "data": {}})
        options = resp["data"]["options"]
        print("\n[~] Sorting Options:")
        for key, name in options.items():
            print(f"   {key}. {name}")
        choice = input("Select sorting method: ").strip()
        resp = self._handler.handle(
            {"action": "set_sorting", "data": {"strategy_key": choice}}
        )
        self._render_message(resp)

    def _handle_wallet_sorting(self):
        resp = self._handler.handle(
            {"action": "get_wallet_sorting_options", "data": {}}
        )
        options = resp["data"]["options"]
        print("\n[~] Wallet Sorting Options:")
        for key, name in options.items():
            print(f"   {key}. {name}")
        choice = input("Select wallet sorting method: ").strip()
        resp = self._handler.handle(
            {"action": "set_wallet_sorting", "data": {"strategy_key": choice}}
        )
        self._render_message(resp)

    #  Filter handler
    def _handle_filter(self):
        print("\n[?] Filter Options:")
        print("   1. Filter by Date")
        print("   2. Filter by Transaction Type")
        print("   3. Filter by Category")
        print("   4. Filter by Amount")
        print("   5. Filter by Description")
        print("   6. View Active Filters")
        print("   7. Remove a Filter")
        print("   8. Clear All Filters")
        print("   0. Back / Cancel")
        choice = input("Select option: ").strip()

        if choice == "0":
            return

        if choice == "1":
            filter_data = InputHandler.get_date_filter()
        elif choice == "2":
            filter_data = InputHandler.get_type_filter()
        elif choice == "3":
            cat_resp = self._handler.handle(
                {"action": "get_categories", "data": {"transaction_type": "income"}}
            )
            income_cats = set(cat_resp["data"]["categories"])
            cat_resp2 = self._handler.handle(
                {"action": "get_categories", "data": {"transaction_type": "expense"}}
            )
            expense_cats = set(cat_resp2["data"]["categories"])
            all_cats = sorted(income_cats | expense_cats | {"Transfer"})
            filter_data = InputHandler.get_category_filter(all_cats)
        elif choice == "4":
            filter_data = InputHandler.get_amount_filter()
        elif choice == "5":
            filter_data = InputHandler.get_description_filter()
        elif choice == "6":
            resp = self._handler.handle({"action": "get_active_filters", "data": {}})
            if resp["status"] == "error":
                self._show_error(resp["message"])
            else:
                filters = resp["data"]["filters"]
                print("\n[?] Active Filters:")
                if not filters:
                    print("   No filters active")
                else:
                    for i, f in enumerate(filters, 1):
                        print(f"   {i}. {f['name']}: {f['description']}")
            return
        elif choice == "7":
            resp = self._handler.handle({"action": "get_active_filters", "data": {}})
            if resp["status"] == "error":
                self._show_error(resp["message"])
                return
            filters = resp["data"]["filters"]
            idx = InputHandler.get_filter_to_remove(filters)
            if idx is not None:
                resp = self._handler.handle(
                    {"action": "remove_filter", "data": {"filter_index": idx}}
                )
                self._render_message(resp)
            return
        elif choice == "8":
            if InputHandler.confirm("Clear all filters?"):
                resp = self._handler.handle({"action": "clear_filters", "data": {}})
                self._render_message(resp)
            return
        else:
            self._show_error("Invalid option")
            return

        if filter_data:
            resp = self._handler.handle({"action": "add_filter", "data": filter_data})
            self._render_message(resp)

    #  Percentages handler
    def _handle_percentages(self):
        resp = self._handler.handle({"action": "get_percentages", "data": {}})
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        data = resp["data"]
        if data.get("empty"):
            self._show_info(data["message"])
            return

        header = "Category Percentages"
        if data.get("has_filters"):
            header += " [FILTERED]"
            self._show_header(header)
            print(f"[?] Filters: {data['filter_summary']}")
        else:
            self._show_header(header)

        if data["income_percentages"]:
            print("\n[+] Income:")
            for cat, pct in sorted(
                data["income_percentages"].items(), key=lambda x: -x[1]
            ):
                print(f"   {cat}: {pct:.1f}%")
        if data["expense_percentages"]:
            print("\n[-] Expenses:")
            for cat, pct in sorted(
                data["expense_percentages"].items(), key=lambda x: -x[1]
            ):
                print(f"   {cat}: {pct:.1f}%")

    #  Wallet handlers
    def _handle_wallets(self):
        resp = self._handler.handle({"action": "get_wallets", "data": {}})
        data = resp["data"]
        wallets = data["wallets"]
        current_name = data["current_wallet_name"]

        print(f"\n[W] Wallets (Sorted by: {data['sorting_strategy']}):")
        if not wallets:
            print("   No wallets")
            return
        for i, w in enumerate(wallets, 1):
            marker = " *" if current_name and w["name"] == current_name else ""
            sign = "+" if w["balance"] >= 0 else ""
            tag = f"[{w['wallet_type'][0].upper()}]"
            print(
                f"   {i}. {tag} {w['name']} ({w['currency']}) - "
                f"{sign}{w['balance']:.2f}{marker}"
            )
        if current_name:
            print(f"\n   * Current wallet: {current_name}")
        print("\n   [R] = Regular, [D] = Deposit")

    def _handle_wallet_detail(self, name: str):
        resp = self._handler.handle(
            {"action": "get_wallet_detail", "data": {"name": name}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return
        self._render_wallet_detail(resp["data"])

    def _handle_add_wallet(self):
        form = InputHandler.get_wallet_input()
        if form is None:
            self._show_error("Wallet creation cancelled")
            return
        resp = self._handler.handle({"action": "add_wallet", "data": form})
        self._render_message(resp)

    def _handle_edit_wallet(self, name: str):
        resp = self._handler.handle(
            {"action": "get_wallet_detail", "data": {"name": name}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        edit_data = InputHandler.get_wallet_edit_input(resp["data"])
        if edit_data is None:
            self._show_error("Edit cancelled")
            return

        edit_data["name"] = name
        resp = self._handler.handle({"action": "edit_wallet", "data": edit_data})
        self._render_message(resp)

    def _handle_delete_wallet(self, name: str):
        resp = self._handler.handle(
            {"action": "get_wallet_detail", "data": {"name": name}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        self._render_wallet_detail(resp["data"])
        if not InputHandler.confirm(
            f"Are you sure you want to delete wallet '{name}'?"
        ):
            self._show_info("Deletion cancelled")
            return

        resp = self._handler.handle({"action": "delete_wallet", "data": {"name": name}})
        self._render_message(resp)

    def _handle_switch_wallet(self, name: str):
        resp = self._handler.handle({"action": "switch_wallet", "data": {"name": name}})
        self._render_message(resp)
        if resp["status"] == "success":
            self._handle_dashboard()

    #  Recurring handlers
    def _handle_add_recurring(self, tt_name: str):
        tt_label = "Income" if tt_name == "income" else "Expense"
        resp = self._handler.handle(
            {"action": "get_categories", "data": {"transaction_type": tt_name}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return
        categories = resp["data"]["categories"]

        form = InputHandler.get_recurring_transaction_input(tt_label, categories)
        if form is None:
            self._show_error("Recurring transaction cancelled")
            return

        form["transaction_type"] = tt_name
        resp = self._handler.handle({"action": "add_recurring", "data": form})
        self._render_message(resp)

    def _handle_recurring_list(self):
        resp = self._handler.handle({"action": "get_recurring_list", "data": {}})
        items = resp["data"]["recurring_transactions"]
        self._show_header("Recurring Transactions")
        if not items:
            print("   No recurring transactions")
            return
        for i, r in enumerate(items, 1):
            print(f"   {i}. {r['summary']}")

    def _handle_show_recurring(self, index: int):
        resp = self._handler.handle(
            {"action": "get_recurring_detail", "data": {"index": index}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return
        self._show_header("Recurring Transaction Details")
        print(resp["data"]["detail"])

    def _handle_edit_recurring(self, index: int):
        resp = self._handler.handle(
            {"action": "get_recurring_detail", "data": {"index": index}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        recurring_data = resp["data"]
        # wallet_name = recurring_data["wallet_name"]
        tt = recurring_data["transaction_type"]

        cat_resp = self._handler.handle(
            {"action": "get_categories", "data": {"transaction_type": tt}}
        )
        categories = cat_resp["data"]["categories"]

        edit_data = InputHandler.get_recurring_edit_input(recurring_data, categories)
        if edit_data is None:
            self._show_info("Edit cancelled")
            return

        edit_data["index"] = index
        resp = self._handler.handle({"action": "edit_recurring", "data": edit_data})
        self._render_message(resp)

    def _handle_delete_recurring(self, index: int):
        resp = self._handler.handle(
            {"action": "get_recurring_detail", "data": {"index": index}}
        )
        if resp["status"] == "error":
            self._show_error(resp["message"])
            return

        self._show_header("Recurring Transaction Details")
        print(resp["data"]["detail"])

        delete_option = InputHandler.get_recurring_delete_option()
        if delete_option is None or delete_option == 0:
            self._show_info("Deletion cancelled")
            return

        resp = self._handler.handle(
            {
                "action": "delete_recurring",
                "data": {"index": index, "delete_option": delete_option},
            }
        )
        self._render_message(resp)

    #  Rendering helpers
    def _show_header(self, text: str):
        print(f"\n{self.SEPARATOR}")
        print(f"  {text}")
        print(self.SEPARATOR)

    @staticmethod
    def _show_success(message: str):
        print(f"\n[OK] {message}")

    @staticmethod
    def _show_error(message: str):
        print(f"\n[!] {message}")

    @staticmethod
    def _show_info(message: str):
        print(f"\n[i] {message}")

    def _render_message(self, resp: dict):
        """Render a simple status + message response."""
        if resp["status"] == "success":
            self._show_success(resp.get("message", "Done"))
        else:
            self._show_error(resp.get("message", "An error occurred"))

    def _render_dashboard(self, data: dict):
        has_filters = data.get("has_filters", False)
        wallet_name = data["wallet_name"]
        currency = data["currency"]

        header = f"Budget Planner Dashboard - {wallet_name}"
        if has_filters:
            header += " [FILTERED]"
        self._show_header(header)

        if has_filters:
            print(f"[?] Active Filters: {data['filter_summary']}")
            print(
                f"   Showing {data['filter_count']} of "
                f"{data['total_count']} transactions"
            )

        # Balance
        balance = data["balance"]
        sign = "+" if balance >= 0 else ""
        label = "Period Balance" if has_filters else "Balance"
        print(f"\n[$] {label}: {sign}{balance:.2f} {currency}")
        print(f"   Income:  +{data['total_income']:.2f}")
        print(f"   Expense: -{data['total_expense']:.2f}")
        if has_filters:
            ob = data["overall_balance"]
            os_sign = "+" if ob >= 0 else ""
            print(f"   (Overall: {os_sign}{ob:.2f})")

        # Category breakdown
        inc_cat = data.get("income_by_category", {})
        exp_cat = data.get("expense_by_category", {})
        inc_pct = data.get("income_percentages", {})
        exp_pct = data.get("expense_percentages", {})

        if not inc_cat and not exp_cat:
            print("\n[i] No transactions yet")
        else:
            if inc_cat:
                print("\n[+] Income by Category:")
                for cat, amt in sorted(inc_cat.items(), key=lambda x: -x[1]):
                    pct = inc_pct.get(cat, 0)
                    print(f"   {cat}: +{amt:.2f} ({pct:.1f}%)")
            if exp_cat:
                print("\n[-] Expenses by Category:")
                for cat, amt in sorted(exp_cat.items(), key=lambda x: -x[1]):
                    pct = exp_pct.get(cat, 0)
                    print(f"   {cat}: -{amt:.2f} ({pct:.1f}%)")

        # Transaction list
        transactions = data.get("transactions", [])
        strat = data.get("sorting_strategy", "")
        total_count = data.get("total_count", 0)
        header_line = f"\n[#] Transactions (Sorted by: {strat})"
        if has_filters:
            header_line += f" [Filtered: {len(transactions)}/{total_count}]"
        print(header_line + ":")
        if has_filters and data.get("filter_summary"):
            print(f"   [?] Filters: {data['filter_summary']}")

        if not transactions:
            if has_filters:
                print("   No transactions match current filters")
            else:
                print("   No transactions")
        else:
            for i, t in enumerate(transactions, 1):
                rec_marker = " (R)" if t.get("recurrence_id") else ""
                print(f"   {i}. {t['display']}{rec_marker}")

    def _render_transaction_detail(self, data: dict):
        self._show_header("Transaction Details")
        sign = data["sign"]
        if data["is_transfer"]:
            direction = "Outgoing" if data["transaction_type"] == "-" else "Incoming"
            print(f"ID: {data['id']}")
            print(f"Type: Transfer ({direction})")
            print(f"Amount: {sign}{abs(data['amount']):.2f}")
            print(f"From: {data.get('from_wallet', '?')}")
            print(f"To: {data.get('to_wallet', '?')}")
            print(f"Description: {data['description'] or 'N/A'}")
            print(f"Date: {data['date']}")
        else:
            type_label = "Income" if data["transaction_type"] == "+" else "Expense"
            if data.get("recurrence_id"):
                type_label += " (Recurring)"
            print(f"ID: {data['id']}")
            print(f"Type: {data['transaction_type']} ({type_label})")
            print(f"Amount: {sign}{abs(data['amount']):.2f}")
            print(f"Category: {data['category']}")
            print(f"Description: {data['description'] or 'N/A'}")
            print(f"Date: {data['date']}")

    def _render_wallet_detail(self, data: dict):
        wt = data["wallet_type"].capitalize()
        self._show_header(f"{wt} Wallet: {data['name']}")
        print(f"   ID:          {data['id']}")
        print(f"   Type:        {wt}")
        print(f"   Name:        {data['name']}")
        print(f"   Currency:    {data['currency']}")
        print(f"   Description: {data['description'] or 'N/A'}")
        print(f"   Created:     {data['created']}")
        b = data["balance"]
        print(f"   Balance:     {'+' if b >= 0 else ''}{b:.2f}")
        print(f"   Income:      +{data['total_income']:.2f}")
        print(f"   Expense:     -{data['total_expense']:.2f}")
        print(f"   Transactions: {data['transaction_count']}")

        dep = data.get("deposit")
        if dep:
            print("\n   --- Deposit Details ---")
            print(f"   Interest Rate:    {dep['interest_rate']:.2f}% per year")
            print(f"   Term:             {dep['term_months']} months")
            print(f"   Capitalization:   {'Yes' if dep['capitalization'] else 'No'}")
            print(f"   Maturity Date:    {dep['maturity_date']}")
            if dep["is_matured"]:
                print("   Status:           MATURED")
            else:
                print(f"   Days to Maturity: {dep['days_until_maturity']} days")
            print(f"\n   Principal:        {dep['principal']:.2f} {data['currency']}")
            print(
                f"   Accrued Interest: {dep['accrued_interest']:.2f} "
                f"{data['currency']}"
            )
            print(
                f"   Total at Maturity: {dep['maturity_amount']:.2f} "
                f"{data['currency']}"
            )

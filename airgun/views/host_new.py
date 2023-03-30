import time

from selenium.webdriver.common.keys import Keys
from widgetastic.widget import Checkbox
from widgetastic.widget import Text
from widgetastic.widget import TextInput
from widgetastic.widget import View
from widgetastic.widget import Widget
from widgetastic.widget.table import Table
from widgetastic_patternfly4 import Button
from widgetastic_patternfly4 import Dropdown
from widgetastic_patternfly4 import Pagination
from widgetastic_patternfly4 import Select
from widgetastic_patternfly4 import Tab
from widgetastic_patternfly4.ouia import BreadCrumb
from widgetastic_patternfly4.ouia import Button as OUIAButton
from widgetastic_patternfly4.ouia import ExpandableTable
from widgetastic_patternfly4.ouia import Modal
from widgetastic_patternfly4.ouia import PatternflyTable

from airgun.views.common import BaseLoggedInView
from airgun.widgets import Accordion
from airgun.widgets import ItemsList
from airgun.widgets import CheckboxGroup
from airgun.widgets import Pf4ActionsDropdown
from airgun.widgets import Pf4ConfirmationDialog
from airgun.widgets import SatTableWithoutHeaders


class SearchInput(TextInput):
    def fill(self, value):
        changed = super().fill(value)
        if changed:
            # workaround for BZ #2140636
            time.sleep(1)
            self.browser.send_keys(Keys.ENTER, self)
        return changed


class RemediationView(Modal):
    """Remediation window view"""

    OUIA_ID = 'OUIA-Generated-Modal-large-1'
    remediate = Button('Remediate')
    cancel = Button('Cancel')
    table = PatternflyTable(
        component_id='OUIA-Generated-Table-4',
        column_widgets={
            'Hostname': Text('.//td[1]'),
            'Recommendation': Text('.//td[2]'),
            'Resolution': Text('.//td[3]'),
            'Reboot Required': Text('.//td[4]'),
        },
    )

    @property
    def is_displayed(self):
        return self.title.wait_displayed()


class Card(View):
    """Each card in host view has it's own title with same locator"""

    title = Text('.//div[@class="pf-c-card__title"]')


class DropdownWithDescripton(Dropdown):
    """Dropdown with description below items"""

    ITEM_LOCATOR = ".//*[contains(@class, 'pf-c-dropdown__menu-item') and contains(text(), {})]"


class HostDetailsCard(Widget):
    """Overview/Details and Details/SystemProperties card body contains multiple host detail information"""

    LABELS = '//div[@class="pf-c-description-list__group"]//dt//span'
    VALUES = '//div[@class="pf-c-description-list__group"]//dd//descendant::*/text()/..'

    def read(self):
        """Return a dictionary where keys are property names and values are property values.
        Values are either in span elements or in div elements
        """
        items = {}
        labels = self.browser.elements(f'{self.parent.ROOT}{self.LABELS}')
        values = self.browser.elements(f'{self.parent.ROOT}{self.VALUES}')
        # the length of elements should be always same
        if len(values) != len(labels):
            raise AttributeError(
                'Each label should have one value, therefore length should be equal. '
                f'But length of labels: {len(labels)} is not equal to length of {len(values)}, '
                'Please double check xpaths.'
            )
        for key, value in zip(labels, values):
            value = self.browser.text(value)
            key = self.browser.text(key).replace(' ', '_').lower()
            items[key] = value
        return items


class NewHostDetailsView(BaseLoggedInView):
    breadcrumb = BreadCrumb('breadcrumbs-list')

    @property
    def is_displayed(self):
        breadcrumb_loaded = self.browser.wait_for_element(self.breadcrumb, exception=False)
        return breadcrumb_loaded and self.breadcrumb.locations[0] == 'Hosts'

    edit = OUIAButton('OUIA-Generated-Button-secondary-1')
    dropdown = Dropdown(locator='//button[@id="hostdetails-kebab"]/..')
    schedule_job = Pf4ActionsDropdown(locator='.//div[div/button[@aria-label="Select"]]')

    @View.nested
    class overview(Tab):
        ROOT = './/div[contains(@class, "host-details-tab-item")]'

        @View.nested
        class details(Card):
            ROOT = './/article[.//div[text()="Details"]]'

            details = HostDetailsCard()

            #TODO  power_operations = 

        @View.nested
        class host_status(Card):
            ROOT = './/article[.//span[text()="Host status"]]'

            status = Text('.//h4[contains(@data-ouia-component-id, "global-state-title")]')
            manage_all_statuses = Text('.//a[normalize-space(.)="Manage all statuses"]')

            status_success = Text('.//a[span[@class="status-success"]]')
            status_warning = Text('.//a[span[@class="status-warning"]]')
            status_error = Text('.//a[span[@class="status-error"]]')
            status_disabled = Text('.//a[span[@class="disabled"]]')

        class recent_audits(Card):
            ROOT = './/article[.//div[text()="Recent audits"]]'

            all_audits = Text('.//a[normalize-space(.)="All audits"]')
            table = SatTableWithoutHeaders(locator='.//table[@aria-label="audits table"]')
        

        @View.nested
        class recent_communication(Card):
            ROOT = './/article[.//div[text()="Recent communication"]]'

            last_checkin_value = Text('.//div[@class="pf-c-description-list__text"]')

        @View.nested
        class errata(Card):
            ROOT = './/article[.//div[text()="Errata"]]'

            enable_repository_sets = Text('.//a[normalize-space(.)="Enable repository sets"]')

        @View.nested
        class content_view_details(Card):
            ROOT = './/article[.//div[text()="Content view details"]]'
            actions = Dropdown(locator='.//div[contains(@class, "pf-c-dropdown")]')

            org_view = Text('.//a[contains(@href, "content_views")]')

        @View.nested
        class installable_errata(Card):
            ROOT = './/article[.//div[text()="Installable errata"]]'

            security_advisory = Text('.//a[contains(@href, "type=security")]')
            bug_fixes = Text('.//a[contains(@href, "type=bugfix")]')
            enhancements = Text('.//a[contains(@href, "type=enhancement")]')

        @View.nested
        class total_risks(Card):
            ROOT = './/article[.//div[text()="Total risks"]]'
            actions = Dropdown(locator='.//div[contains(@class, "pf-c-dropdown")]')

            low = Text('.//*[@id="legend-labels-0"]/*')
            moderate = Text('.//*[@id="legend-labels-1"]/*')
            important = Text('.//*[@id="legend-labels-2"]/*')
            critical = Text('.//*[@id="legend-labels-3"]/*')

        @View.nested
        class recent_jobs(Card):
            ROOT = './/article[.//div[text()="Recent jobs"]]'
            actions = Dropdown(locator='.//div[contains(@class, "pf-c-dropdown")]')

            class finished(Tab):
                table = SatTableWithoutHeaders(locator='.//table[@aria-label="recent-jobs-table"]')

            class running(Tab):
                table = SatTableWithoutHeaders(locator='.//table[@aria-label="recent-jobs-table"]')

            class scheduled(Tab):
                table = SatTableWithoutHeaders(locator='.//table[@aria-label="recent-jobs-table"]')

        @View.nested
        class system_purpose(Card):
            ROOT = './/article[.//div[text()="System purpose"]]'
            edit_system_purpose = Text('.//button[@data-ouia-component-id="syspurpose-edit-button"]')

            role = Text('.//dd[contains(@class, "pf-c-description-list__description")][1]')
            sla = Text('.//dd[contains(@class, "pf-c-description-list__description")][2]')
            usage_type = Text('.//dd[contains(@class, "pf-c-description-list__description")][3]')
            release_version = Text('.//dd[contains(@class, "pf-c-description-list__description")][4]')
            addons = Text('.//dd[contains(@class, "pf-c-description-list__description")][5]')


    @View.nested
    class details(Tab):
        ROOT = './/div[contains(@class, "host-details-tab-item")]'

        card_collapse_switch = Text('.//button[contains(@data-ouia-component-id, "expand-button")]')

        @View.nested
        class system_properties(Card):
            ROOT = './/article[.//div[text()="System properties"]]'

            sys_properties = HostDetailsCard()

        @View.nested
        class operating_system(Card):
            ROOT = './/article[.//div[text()="Operating system"]]'

            architecture = Text('.//a[contains(@data-ouia-component-id, "OUIA-Generated-Button-link-1")]')
            os = Text('.//a[contains(@data-ouia-component-id, "OUIA-Generated-Button-link-2")]')
            boot_time = Text('.//div[contains(@class, "pf-c-description-list__group")][3]/dd/div')
            kernel_release = Text('.//div[contains(@class, "pf-c-description-list__group")][4]/dd/div')

        @View.nested
        class provisioning(Card):
            ROOT = './/article[.//div[text()="Provisioning"]]'

            build_duration = Text('.//div[contains(@class, "pf-c-description-list__group")][1]/dd/div')
            token = Text('.//div[contains(@class, "pf-c-description-list__group")][2]/dd/div')
            pxe_loader = Text('.//div[contains(@class, "pf-c-description-list__group")][3]/dd/div')

        @View.nested
        class bios(Card):
            ROOT = './/article[.//div[text()="BIOS"]]'

            vendor = Text('.//div[contains(@class, "pf-c-description-list__group")][1]/dd/div')
            version = Text('.//div[contains(@class, "pf-c-description-list__group")][2]/dd/div')
            release_date = Text('.//div[contains(@class, "pf-c-description-list__group")][3]/dd/div')

        @View.nested
        class registration_details(Card):
            ROOT = './/article[.//div[text()="Registration details"]]'

            registered_on = Text('.//div[contains(@class, "pf-c-description-list__group")][1]/dd/div')
            registered_by = ItemsList('.//div[contains(@class, "pf-c-description-list__group")][2]/ul')
            activation_key_link = Text('.//div[contains(@class, "pf-c-description-list__group")][2]//a')
            registered_through = Text('.//div[contains(@class, "pf-c-description-list__group")][3]/dd/div')

        @View.nested
        class hw_properties(Card):
            ROOT = './/article[.//div[text()="HW properties"]]'

            model = Text('.//div[contains(@class, "pf-c-description-list__group")][1]//dd')
            number_of_cpus = Text('.//div[contains(@class, "pf-c-description-list__group")][2]//dd')
            sockets = Text('.//div[contains(@class, "pf-c-description-list__group")][3]//dd')
            cores_per_socket = Text('.//div[contains(@class, "pf-c-description-list__group")][4]//dd')
            ram = Text('.//div[contains(@class, "pf-c-description-list__group")][5]//dd')

        @View.nested
        class provisioning_templates(Card):
            ROOT = './/article[.//div[text()="Provisioning templates"]]'

            templates_table = SatTableWithoutHeaders(locator='.//table[@aria-label="templates table"]')

        @View.nested
        class installed_products(Card):
            ROOT = './/article[.//div[text()="Installed products"]]'

            installed_products_list = ItemsList(locator='.//ul[contains(@class, "pf-c-list")]')

        @View.nested
        class networking_interfaces(Card):
            ROOT = './/article[.//div[text()="Networking interfaces"]]'

            # TODO Finish Accordion correctly
            networking_interfaces_accordion = Accordion(locator='.//div[contains(@class, "pf-c-card__expandable-content")]')
            #networking_interfaces_accordion = Accordion(locator='.//dl[contains(@class, "pf-c-accordion interface-accordion")]')
            networking_interfaces_dict = {
                'fqdn': Text('.//div[contains(@class, "pf-c-accordion__expanded-content-body")]//div[.//dt[normalize-space(.)="FQDN"]]//div'),
                'ipv4': Text('.//div[contains(@class, "pf-c-accordion__expanded-content-body")]//div[.//dt[normalize-space(.)="IPv4"]]//div'),
                'ipv6': Text('.//div[contains(@class, "pf-c-accordion__expanded-content-body")]//div[.//dt[normalize-space(.)="IPv6"]]//div'),
                'mac': Text('.//div[contains(@class, "pf-c-accordion__expanded-content-body")]//div[.//dt[normalize-space(.)="MAC"]]//div'),
                'subnet': Text('.//div[contains(@class, "pf-c-accordion__expanded-content-body")]//div[.//dt[normalize-space(.)="Subnet"]]//div'),
                'mtu': Text('.//div[contains(@class, "pf-c-accordion__expanded-content-body")]//div[.//dt[normalize-space(.)="MTU"]]//div')
            }
            edit_interfaces = Text('.//a[contains(@href, "/hosts/")]')

        @View.nested
        class networking_interface(Card):
            pass    

    @View.nested
    class content(Tab):
        # TODO Setting ROOT is just a workaround because of BZ 2119076,
        # once this gets fixed we should use the parametrized locator from Tab class
        ROOT = './/div'

        @View.nested
        class packages(Tab):
            # workaround for BZ 2119076
            ROOT = './/div[@id="packages-tab"]'

            select_all = Checkbox(locator='.//div[@id="selection-checkbox"]/div/label')
            searchbar = SearchInput(locator='.//input[contains(@class, "pf-m-search")]')
            status_filter = Dropdown(locator='.//div[@aria-label="select Status container"]/div')
            upgrade = Pf4ActionsDropdown(
                locator='.//div[div/button[normalize-space(.)="Upgrade"]]'
            )
            dropdown = Dropdown(locator='.//div[button[@aria-label="bulk_actions"]]')

            table = PatternflyTable(
                component_id="host-packages-table",
                column_widgets={
                    0: Checkbox(locator='.//input[@type="checkbox"]'),
                    'Package': Text('./parent::td'),
                    'Status': Text('./span'),
                    'Installed version': Text('./parent::td'),
                    'Upgradable to': Text('./span'),
                    5: Dropdown(locator='.//div[contains(@class, "pf-c-dropdown")]'),
                },
            )
            pagination = Pagination()

        @View.nested
        class errata(Tab):
            # workaround for BZ 2119076
            ROOT = './/div[@id="errata-tab"]'

            select_all = Checkbox(locator='.//div[@id="selection-checkbox"]/div/label')
            searchbar = SearchInput(locator='.//input[contains(@class, "pf-m-search")]')
            type_filter = Select(locator='.//div[@aria-label="select Type container"]/div')
            severity_filter = Select(locator='.//div[@aria-label="select Severity container"]/div')
            apply = Pf4ActionsDropdown(locator='.//div[@aria-label="errata_dropdown"]')
            dropdown = Dropdown(locator='.//div[button[@aria-label="bulk_actions"]]')

            table = ExpandableTable(
                component_id="host-errata-table",
                column_widgets={
                    1: Checkbox(locator='.//input[@type="checkbox"]'),
                    'Errata': Text('./a'),
                    'Type': Text('./span'),
                    'Severity': Text('./span'),
                    'Installable': Text('./span'),
                    'Synopsis': Text('./span'),
                    'Published date': Text('./span/span'),
                    8: Dropdown(locator='./div'),
                },
            )
            pagination = Pagination()

        @View.nested
        class module_streams(Tab):
            TAB_NAME = 'Module streams'
            # workaround for BZ 2119076
            ROOT = './/div[@id="modulestreams-tab"]'

            searchbar = SearchInput(locator='.//input[contains(@class, "pf-m-search")]')
            status_filter = Select(locator='.//div[@aria-label="select Status container"]/div')
            installation_status_filter = Select(
                locator='.//div[@aria-label="select Installation status container"]/div'
            )
            dropdown = Dropdown(locator='.//div[button[@aria-label="bulk_actions"]]')

            table = Table(
                locator='.//table[@aria-label="Content View Table"]',
                column_widgets={
                    'Name': Text('./a'),
                    'State': Text('.//span'),
                    'Stream': Text('./parent::td'),
                    'Installation status': Text('.//small'),
                    'Installed profile': Text('./parent::td'),
                    5: DropdownWithDescripton(locator='.//div[contains(@class, "pf-c-dropdown")]'),
                },
            )
            pagination = Pagination()

        @View.nested
        class repository_sets(Tab):
            TAB_NAME = 'Repository sets'
            # workaround for BZ 2119076
            ROOT = './/div[@id="repo-sets-tab"]'    

            select_all = Checkbox(locator='.//div[@id="selection-checkbox"]/div/label')
            searchbar = SearchInput(locator='.//input[contains(@class, "pf-m-search")]')
            status_filter = Select(locator='.//div[@aria-label="select Status container"]/div')
            dropdown = Dropdown(locator='.//div[button[@aria-label="bulk_actions"]]')

            table = Table(
                locator='.//table[@aria-label="Content View Table"]',
                column_widgets={
                    0: Checkbox(locator='.//input[@type="checkbox"]'),
                    'Repository': Text('./span'),
                    'Product': Text('./a'),
                    'Repository path': Text('./span'),
                    'Status': Text('.//span[contains(@class, "pf-c-label__content")]'),
                    5: Dropdown(locator='.//div[contains(@class, "pf-c-dropdown")]'),
                },
            )
            pagination = Pagination()

    @View.nested
    class parameters(Tab):
        ROOT = './/div'

        add_parameter = OUIAButton('OUIA-Generated-Button-primary-4')
        searchbar = SearchInput(locator='//input[contains(@class, "pf-c-search-input__text-input")]')
        # TODO solve case while adding new parameter. I need to somehow specify if that cell in that column should be Text() or TextInput() etc.
        parameters_table = Table(
            locator='.//table[@aria-label="Parameters table"]',
            column_widgets={
                'Name': Text('.//td[contains(@data-label, "Name")]'),
                'Type': Text('.//td[contains(@data-label, "Type")]'),
                'Value': Text('.//td[contains(@data-label, "Value")]'),
                'Source': Text('.//td[contains(@data-label, "Source")]'),
                4: Button(locator='.//button[contains(@data-ouia-component-id, "OUIA-Generated-Button-plain-")]'),
                5: Button(locator='.//td[contains(@class, "parameters-actions")]//button'),
            }
        )
        pagination = Pagination()

    @View.nested
    class traces(Tab):
        ROOT = './/div'

        title = Text('//h2')
        enable_traces = OUIAButton('enable-traces-button')
        select_all = Checkbox(locator='.//input[contains(@aria-label, "Select all")]')
        searchbar = SearchInput(locator='.//input[contains(@aria-label, "Select all")]')
        Pf4ActionsDropdown = Button(locator='.//div[contains(@aria-label, "bulk_actions_dropdown")]')
        traces_table = PatternflyTable(
            #locator='.//table[contains(@class, "pf-c-table")]',
            component_id='host-traces-table',
            column_widgets={
            0: Checkbox(locator='.//input[contains(@aria-label, "Select row")]'),
            'Application': Text('.//td[2]'),
            'Type': Text('.//td[3]'),
            'Helper': Text('.//td[4]'),
            4: Button(locator='.//button[contains(@aria-label, "Actions")]')
            }
        )
        pagination = Pagination()
        

    @View.nested
    class ansible(Tab):
        """View comprising the subtabs under the Ansible Tab"""

        ROOT = './/div'

        @View.nested
        class roles(Tab):
            TAB_NAME = 'Roles'
            ROOT = './/div[@class="ansible-host-detail"]'

            assignedRoles = Text('.//a[contains(@href, "roles/all")]')
            edit = Button(locator='.//button[@aria-label="edit ansible roles"]')
            table = Table(
                locator='.//table[contains(@class, "pf-c-table")]',
                column_widgets={'Name': Text('.//a')},
            )
            pagination = Pagination()

        @View.nested
        class variables(Tab):
            TAB_NAME = 'Variables'
            ROOT = './/div[@class="ansible-host-detail"]'
            table = Table(
                locator='.//table[contains(@class, "pf-c-table")]',
                column_widgets={
                    'Name': Text('.//a'),
                    'Ansible role': Text('./span'),
                    'Type': Text('./span'),
                    # the next field can also be a form group
                    'Value': Text('./span'),
                    'Source attribute': Text('./span'),
                    # The next 2 buttons are hidden by default, but appear in this order
                    5: Button(locator='.//button[@aria-label="Cancel editing override button"]'),
                    6: Button(locator='.//button[@aria-label="Submit override button"]'),
                    # Clicking this button hides it, and displays the previous 2
                    7: Button(locator='.//button[@aria-label="Edit override button"]'),
                },
            )
            pagination = Pagination()

        @View.nested
        class inventory(Tab):
            TAB_NAME = 'Inventory'
            ROOT = './/div[@class="ansible-host-detail"]'

        @View.nested
        class jobs(Tab):
            TAB_NAME = 'Jobs'
            ROOT = './/div[@class="ansible-host-detail"]'

            @property
            def is_displayed(self):
                return (
                    self.schedule.is_displayed
                    or self.jobs.is_displayed
                    or self.previous.is_displayed
                )

            @View.nested
            class schedule(Tab):
                # Only displays when there isn't a Job scheduled for this host
                scheduleRecurringJob = Button(
                    locator='.//button[@aria-label="schedule recurring job"]'
                )

                @property
                def is_displayed(self):
                    return self.scheduleRecurringJob.is_displayed

            @View.nested
            class jobs(Tab):
                # Mutually Exclusive with the above button
                scheduledText = './/h3[text()="Scheduled recurring jobs"]'
                scheduledJobsTable = Table(
                    locator='.//div[contains(@class, "pf-c-table)"]',
                    column_widgets={
                        'Description': Text('.//a'),
                        'Schedule': Text('./span'),
                        'Next Run': Text('./span'),
                        4: Dropdown(locator='.//div[contains(@class, "pf-c-dropdown")]'),
                    },
                )
                pagination = Pagination()

                @property
                def is_displayed(self):
                    return self.scheduledText.is_displayed

            @View.nested
            class previous(Tab):
                # Only displayed on Refresh when there are previously executed jobs
                previousText = './/h3[text()="Previously executed jobs"]'
                previousJobsTable = Table(
                    locator='',
                    column_widgets={
                        'Description': Text('.//a'),
                        'Result': Text('./span'),
                        'State': Text('./span'),
                        'Executed at': Text('./span'),
                        'Schedule': Text('./span'),
                    },
                )
                pagination = Pagination()

                @property
                def is_displayed(self):
                    return self.previousText.is_displayed

    @View.nested
    class reports(Tab):
        ROOT = './/div'

        search_bar = SearchInput(locator='.//input[contains(@class, "search-input")]')
        reports_table = PatternflyTable(
            component_id='reports-table',
            column_widgets={
                'reported_at': Text('.//a'),
                'failed': Text('.//td[2]'),
                'failed_restarts': Text('.//td[3]'),
                'restarted': Text('.//td[4]'),
                'applied': Text('.//td[5]'),
                'skipped': Text('.//td[6]'),
                'origin': Text('.//td[7]'),
                'pending': Text('.//td[8]'),
                8: Button(locator='.//button[contains(@aria-label, "Actions")]'),
            }
        )

        pagination = Pagination()

    @View.nested
    class insights(Tab):
        ROOT = './/div'

        search_bar = SearchInput(locator='.//input[contains(@class, "search-input")]')
        remediate = OUIAButton('OUIA-Generated-Button-primary-5')
        insights_dropdown = Dropdown(locator='.//div[contains(@class, "insights-dropdown")]')

        select_all = Checkbox(locator='.//input[@name="check-all"]')
        recommendations_table = PatternflyTable(
            component_id='OUIA-Generated-Table-2',
            column_widgets={
                0: Checkbox(locator='.//input[@type="checkbox"]'),
                'Recommendation': Text('.//td[2]'),
                'Total Risk': Text('.//td[3]'),
                'Remediate': Text('.//td[4]'),
                4: Button(locator='.//button[contains(@aria-label, "Actions")]')
            }
        )
        pagination = Pagination()
        remediation_window = View.nested(RemediationView)


class InstallPackagesView(View):
    """Install packages modal"""

    ROOT = './/div[@id="package-install-modal"]'

    select_all = Checkbox(locator='.//div[@id="selection-checkbox"]/div/label')
    searchbar = SearchInput(locator='.//input[contains(@class, "pf-m-search")]')

    table = Table(
        locator='.//table[@aria-label="Content View Table"]',
        column_widgets={
            0: Checkbox(locator='.//input[@type="checkbox"]'),
            'Package': Text('./parent::td'),
            'Version': Text('./parent::td'),
        },
    )
    pagination = Pagination()

    install = Button(locator='.//button[(normalize-space(.)="Install")]')
    cancel = Button('Cancel')


class AllAssignedRolesView(View):
    """All Assigned Roles Modal"""

    ROOT = './/div[@data-ouia-component-id="modal-ansible-roles"]'

    table = Table(
        locator='.//table[contains(@class, "pf-c-table")]',
        column_widgets={'Name': Text('.//a'), 'Source': Text('.//a')},
    )
    pagination = Pagination()


class EnableTracerView(View):
    """Enable Tracer Modal"""

    ROOT = './/div[@data-ouia-component-id="enable-tracer-modal"]'

    confirm = Button(locator='//*[@data-ouia-component-id="enable-tracer-modal"]/footer/button[1]')


class EditAnsibleRolesView(View):
    """Edit Ansible Roles Modal"""

    ROOT = ''
    # No current representation for this Widget in Widgetastic


class ModuleStreamDialog(Pf4ConfirmationDialog):

    confirm_dialog = Button(locator='.//button[@aria-label="confirm-module-action"]')
    cancel_dialog = Button(locator='.//button[@aria-label="cancel-module-action"]')


class RecurringJobDialog(Pf4ConfirmationDialog):

    confirm_dialog = Button(locator='.//button[@data-ouia-component-id="btn-modal-confirm"]')
    cancel_dialog = Button(locator='.//button[@data-ouia-component-id="btn-modal-cancel"]')


class PF4CheckboxTreeView(CheckboxGroup):
    """
    Modified :class:`airgun.widgets.CheckboxGroup` for PF4 tree view with checkboxes:
        https://www.patternfly.org/v4/components/tree-view#with-checkboxes
    """

    ITEMS_LOCATOR = './/*[self::span|self::label][contains(@class, "pf-c-tree-view__node-text")]'
    CHECKBOX_LOCATOR = (
        './/*[self::span|self::label][contains(@class, "pf-c-tree-view__node-text")]'
        '[normalize-space(.)="{}"]/preceding-sibling::span/input[@type="checkbox"]'
    )


class ManageColumnsView(BaseLoggedInView):
    """Manage columns modal."""

    ROOT = '//div[contains(@class, "pf-c-modal-box")]'

    CHECKBOX_SECTION_TOGGLE = (
        './/*[self::span|self::label][contains(@class, "pf-c-tree-view__node-text")]'
        '[normalize-space(.)="{}"]/preceding-sibling::button'
    )
    DEFAULT_COLLAPSED_SECTIONS = [
        CHECKBOX_SECTION_TOGGLE.format('Content'),
        CHECKBOX_SECTION_TOGGLE.format('Network'),
        CHECKBOX_SECTION_TOGGLE.format('Reported data'),
        CHECKBOX_SECTION_TOGGLE.format('RH Cloud'),
    ]
    is_tree_collapsed = True
    title = Text(
        './/header//span[contains(@class, "pf-c-modal-box__title")]'
        '[normalize-space(.)="Manage columns"]'
    )
    confirm_dialog = Button(locator='.//button[normalize-space(.)="Save"]')
    cancel_dialog = Button(locator='.//button[normalize-space(.)="Cancel"]')
    checkbox_group = PF4CheckboxTreeView(locator='.//div[contains(@class, "pf-c-tree-view")]')

    def collapsed_sections(self):
        return (self.browser.element(locator) for locator in self.DEFAULT_COLLAPSED_SECTIONS)

    @property
    def is_displayed(self):
        title = self.browser.wait_for_element(self.title, exception=False)
        return title is not None and title.is_diaplyed()

    def expand_all(self):
        """Expand all tree sections that are collapsed by default"""
        if self.is_tree_collapsed:
            for checkbox_group in self.collapsed_sections():
                checkbox_group.click()
                self.is_tree_collapsed = False

    def read(self):
        """
        Get labels and values of all checkboxes in the dialog.

        :return dict: mapping of `label: value` items
        """
        self.expand_all()
        return self.checkbox_group.read()

    def fill(self, values):
        """
        Set value of given checkboxes.
        Example: values={'Operating system': True, 'Owner': False}

        :param dict values: mapping of `label: value` items
        """
        self.expand_all()
        self.checkbox_group.fill(values)

    def submit(self):
        """Submit the dialog and wait for the page to reload."""
        self.confirm_dialog.click()
        # the submit and page reload does not kick in immediately
        # so ensure_page_safe() does not catches it
        time.sleep(2)
        self.browser.plugin.ensure_page_safe()

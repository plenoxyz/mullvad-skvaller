import dictdiffer


class MullvadDiff():
    def __init__(self, old_data, new_data):
        self.changes = []
        self.old_data = self.__mv_data_to_dict(old_data)
        self.new_data = self.__mv_data_to_dict(new_data)

    def __mv_data_to_dict(self, data):
        """Converts the data from a list of dictionaries to
        a dictionary of dictionaries with the hostname as the
        key, so we can easily compare the data.
        """
        return { relay['hostname']: relay for relay in data }

    def gen_changes(self):
        """Generates the changes between the old and new data
        and calls the appropriate function to generate info needed
        for the notification and message
        """
        diffs = list(dictdiffer.diff(
            self.old_data,
            self.new_data,
            dot_notation=False
        )) 

        if not diffs:
            return []

        # new root keys
        new_servers = [diff[2] for diff in diffs
            if diff[0] == 'add' and diff[1] == []][0]
        
        # removed root keys
        removed_servers = [diff[2] for diff in diffs
            if diff[0] == 'remove' and diff[1] == []][0]
        
        # new values in existing root keys
        changed_values = [diff for diff in diffs
            if diff[0] == 'add' and diff[1] != []] + [
            # removed values in existing root keys
            diff for diff in diffs
            if diff[0] == 'remove' and diff[1] != []] + [
            # changed values in existing root keys
            diff for diff in diffs
            if diff[0] == 'change']

        # render the notification messages
        for diff in new_servers:
            self.__render_server_change(diff, data=self.new_data, action='added')
        for diff in removed_servers:
            self.__render_server_change(diff, data=self.old_data, action='removed')
        for diff in changed_values:
            self.__render_spec_change(diff, self.new_data)
        
        return self.changes


    def __render_server_change(self, diff, data, action):
        """Renders the server change notification message.\n
        Root key changes (this case) are single line messages.
        """
        server = diff[0]
        city_name = data[server].get('city_name')
        country_name = data[server].get('country_name')
        country_code = data[server].get('country_code')
        provider = data[server].get('provider')
        network_port_speed = data[server].get('network_port_speed')
        owned = data[server].get('owned')

        message = f'**{server}** has been {action}' \
            + (f' in ' if any([city_name, country_name]) else '') \
            + (f'{str(city_name)}' if city_name else '') \
            + (f', ' if all([city_name, country_name]) else '') \
            + (f'**{str(country_name)}**' if country_name else '') \
            + (f' hosted on {str(provider)}' if provider else '') \
            + (f' at {str(network_port_speed)} Gbps' if network_port_speed else '') \
            + (f' (owned by Mullvad)' if owned else ' (Rented)')

        self.changes.append({
            'server': server,
            'country_name': country_name,
            'country_code': country_code,
            'message': message
        })


    def __render_spec_change(self, diff, new_data):
        """Renders the server change notification message.\n
        Server key changes (this case) are multi-line messages
        so we it might append to existing changes instead of 
        creating a new one.
        """
        server = diff[1][0]
        action = diff[0]

        if action == 'add' or action == 'remove':
            action = 'added' if action == 'add' else 'removed'
            key = diff[2][0][0]
            value = diff[2][0][1]
            list_message = f'\n- {action} `{key}` with `{value}`'

        if action == 'change':
            action = 'changed'
            key = diff[1][1]
            old_value = diff[2][0]
            new_value = diff[2][1]
            list_message = f'\n- {action} `{key}`' \
                + f' from `{old_value}` to `{new_value}`'

        # if entry already exists in changes,
        # append to the existing message
        for change in self.changes:
            if change['server'] == server:
                change['message'] += list_message
                return

        city_name = new_data.get(server).get('city_name')
        country_name = new_data.get(server).get('country_name')
        country_code = new_data.get(server).get('country_code')

        message = f'**{server}** changed the following values' \
            + (f' in ' if any([city_name, country_name]) else '') \
            + (f'{str(city_name)}' if city_name else '') \
            + (f', ' if all([city_name, country_name]) else '') \
            + (f'**{str(country_name)}**' if country_name else '') + ':' \
            + list_message

        self.changes.append({
            'server': server,
            'country_name': country_name,
            'country_code': country_code,
            'message': message
        })

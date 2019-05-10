Method.value = 'method.value'
Method.properties = {'Enabled': 'True','Items': 'method.values'}
Show_Methods.action = {True: 'self.show_methods()'}
Show_Methods.properties = {'Enabled': 'True'}
File.value = 'collect.basename'
File.properties = {'Enabled': 'True'}
Extension.value = 'collect.xray_image_extension'
Extension.properties = {'Enabled': 'True'}
Description.value = 'collect.description'
Description.properties = {'Enabled': 'True'}
Logfile.value = 'collect.logfile_basename'
Logfile.properties = {'Enabled': 'True'}
Path.value = 'collect.directory'
Path.properties = {'Enabled': 'True'}
Info.properties = {'Label': 'collect.info_message','Enabled': 'True'}
Status.properties = {'Label': 'collect.status_message','Enabled': 'True'}
Actual.properties = {'Label': 'collect.actual_message','Enabled': 'True'}
Generate_Packets.value = 'collect.generating_packets'
Generate_Packets.properties = {
    'Enabled': 'True',
    'Label': [
        ('Cancel Generate', 'collect.generating_packets'),
        ('Cancelled', 'collect.generating_packets and collect.cancelled'),
    ],
}
Collect_Dataset.value = 'collect.collecting_dataset'
Collect_Dataset.properties = {
    'Enabled': [
        (True, 'not collect.dataset_complete'),
    ],
    'Label': [
        ('Cancel Collect', 'collect.collecting_dataset'),
        ('Cancelled', 'collect.collecting_dataset and collect.cancelled'),
        ('Resume Dataset', 'len(collect.xray_images_collected) > 0'),
        ('Dataset Complete', 'collect.dataset_complete'),
    ],
}
Cancel.action = {True: 'collect.cancelled = True'}
Cancel.properties = {
    'Enabled': [(True, 'collect.collecting or collect.generating_packets')],
    'Label': [
        ('Cancelled', 'collect.cancelled'),
    ],
}
Erase_Dataset.value = 'collect.erasing_dataset'
Erase_Dataset.properties = {
    'Enabled': 'not collect.collecting and collect.dataset_started',
    'Label': [
        ('Cancel Erase', 'collect.erasing_dataset'),
        ('Cancelled', 'collect.erasing_dataset and collect.cancelled'),
    ],
}
Finish_Series.value = 'collect.finish_series'
Finish_Series.properties = {'Enabled': 'False'}
Finish_Series_Variable.value = 'collect.finish_series_variable'
Finish_Series_Variable.properties = {
    'Enabled': 'True',
    'Items': 'collect.collection_variables',
}

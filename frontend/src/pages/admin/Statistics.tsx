import { Card, Typography } from 'antd';

const { Title } = Typography;

export default function StatisticsPage() {
  return (
    <Card>
      <Title level={2}>Statistics</Title>
      <p>Statistics dashboard - system metrics and reports</p>
    </Card>
  );
}
